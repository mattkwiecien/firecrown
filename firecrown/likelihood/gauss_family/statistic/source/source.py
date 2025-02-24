"""Abstract base classes for GaussianFamily statistics.

"""

from __future__ import annotations
from typing import Optional, Sequence, final
from abc import abstractmethod
import sacc

import pyccl
import pyccl.nl_pt

from .....modeling_tools import ModelingTools
from .....parameters import ParamsMap
from .....updatable import Updatable


class SourceSystematic(Updatable):
    """An abstract systematic class (e.g., shear biases, photo-z shifts, etc.).

    This class currently has no methods at all, because the argument types for
    the `apply` method of different subclasses are different."""

    def read(self, sacc_data: sacc.Sacc):
        """This method is called to allow the systematic object to read from the
        appropriated sacc data."""


class Source(Updatable):
    """An abstract source class (e.g., a sample of lenses).

    Parameters
    ----------
    systematics : list of str, optional
        A list of the source-level systematics to apply to the source. The
        default of `None` implies no systematics.
    """

    systematics: Sequence[SourceSystematic]
    cosmo_hash: Optional[int]
    tracers: Sequence[Tracer]

    @final
    def read(self, sacc_data: sacc.Sacc):
        """Read the data for this source from the SACC file."""
        if hasattr(self, "systematics"):
            for systematic in self.systematics:
                systematic.read(sacc_data)
        self._read(sacc_data)

    @abstractmethod
    def _read(self, sacc_data: sacc.Sacc):
        """Abstract method to read the data for this source from the SACC file."""

    def _update_source(self, params: ParamsMap):
        """Method to update the source from the given ParamsMap. Any subclass
        that needs to do more than update its contained :python:`Updatable`
        objects should implement this method."""

    @abstractmethod
    def _reset_source(self):
        """Abstract method to reset the source."""

    @final
    def _update(self, params: ParamsMap):
        """Implementation of Updatable interface method `_update`.

        This clears the current hash and tracer, and calls the abstract method
        `_update_source`, which must be implemented in all subclasses."""
        self.cosmo_hash = None
        self.tracers = []
        self._update_source(params)

    @final
    def _reset(self) -> None:
        """Implementation of the Updatable interface method `_reset`.

        This calls the abstract method `_reset_source`, which must be implemented by
        all subclasses."""
        self._reset_source()

    @abstractmethod
    def get_scale(self) -> float:
        """Abstract method to return the scales for this `Source`."""

    @abstractmethod
    def create_tracers(self, tools: ModelingTools):
        """Abstract method to create tracers for this `Source`, for the given
        cosmology."""

    @final
    def get_tracers(self, tools: ModelingTools) -> Sequence[Tracer]:
        """Return the tracer for the given cosmology.

        This method caches its result, so if called a second time with the same
        cosmology, no calculation needs to be done."""

        ccl_cosmo = tools.get_ccl_cosmology()

        cur_hash = hash(ccl_cosmo)
        if hasattr(self, "cosmo_hash") and self.cosmo_hash == cur_hash:
            return self.tracers

        self.tracers, _ = self.create_tracers(tools)
        self.cosmo_hash = cur_hash
        return self.tracers


class Tracer:
    """Bundles together a pyccl.Tracer object with optional information about the
    underlying 3D field, a pyccl.nl_pt.PTTracer, and halo profiles."""

    @staticmethod
    def determine_field_name(field: Optional[str], tracer: Optional[str]) -> str:
        """This function encapsulates the policy for determining the value to be
        assigned to the :python:`field` member variable of a :python:`Tracer`.

        It is a static method only to keep it grouped with the class for which it is
        defining the initialization policy.
        """
        if field is not None:
            return field
        if tracer is not None:
            return tracer
        return "delta_matter"

    def __init__(
        self,
        tracer: pyccl.Tracer,
        tracer_name: Optional[str] = None,
        field: Optional[str] = None,
        pt_tracer: Optional[pyccl.nl_pt.PTTracer] = None,
        halo_profile: Optional[pyccl.halos.HaloProfile] = None,
        halo_2pt: Optional[pyccl.halos.Profile2pt] = None,
    ):
        """Initialize a new Tracer based on the given pyccl.Tracer which must not be
        None.

        Note that the :python:`pyccl.Tracer` is not copied; we store a reference to the
        original tracer. Be careful not to accidentally share :python:`pyccl.Tracer`s.

        If no tracer_name is supplied, then the tracer_name is set to the name of the
        :python:`pyccl.Tracer` class that was used.

        If no field is given, then field is set to either (1) the tracer_name, if one
        was given,, or (2) 'delta_matter'.
        """
        assert tracer is not None
        self.ccl_tracer = tracer
        self.tracer_name: str = tracer_name or tracer.__class__.__name__
        self.field = Tracer.determine_field_name(field, tracer_name)
        self.pt_tracer = pt_tracer
        self.halo_profile = halo_profile
        self.halo_2pt = halo_2pt

    @property
    def has_pt(self) -> bool:
        """Return True if we have a pt_tracer, and False if not."""
        return self.pt_tracer is not None

    @property
    def has_hm(self) -> bool:
        """Return True if we have a halo_profile, and False if not."""
        return self.halo_profile is not None
