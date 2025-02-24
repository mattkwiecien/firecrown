"""Tests for the cluster module."""

from typing import Any, Dict
import itertools
import math

import pytest
import pyccl as ccl
import numpy as np

from firecrown.models.cluster_mass import ClusterMass, ClusterMassArgument
from firecrown.models.cluster_redshift import ClusterRedshift, ClusterRedshiftArgument
from firecrown.models.cluster_mass_true import ClusterMassTrue
from firecrown.models.cluster_abundance import ClusterAbundance
from firecrown.models.cluster_mass_rich_proxy import ClusterMassRich
from firecrown.models.cluster_redshift_spec import ClusterRedshiftSpec
from firecrown.parameters import ParamsMap


@pytest.fixture(name="ccl_cosmo")
def fixture_ccl_cosmo():
    """Fixture for a CCL cosmology object."""

    return ccl.Cosmology(
        Omega_c=0.22, Omega_b=0.0448, h=0.71, sigma8=0.8, n_s=0.963, Neff=3.44
    )


@pytest.fixture(name="parameters")
def fixture_parameters():
    """Fixture for a parameter map."""

    parameters = ParamsMap(
        {
            "mu_p0": 3.19,
            "mu_p1": 0.8,
            "mu_p2": 0.0,
            "sigma_p0": 0.3,
            "sigma_p1": 0.8,
            "sigma_p2": 0.0,
        }
    )
    return parameters


@pytest.fixture(name="z_args")
def fixture_cluster_z_args(parameters):
    """Fixture for cluster redshifts."""
    z_bins = np.array([0.2000146, 0.31251036, 0.42500611, 0.53750187, 0.64999763])
    cluster_z = ClusterRedshiftSpec()
    assert isinstance(cluster_z, ClusterRedshift)

    z_args = cluster_z.gen_bins_by_array(z_bins)

    cluster_z.update(parameters)

    return z_args


@pytest.fixture(name="logM_args")
def fixture_cluster_mass_logM_args(parameters):
    """Fixture for cluster masses."""
    logM_bins = np.array([13.0, 13.5, 14.0, 14.5, 15.0])
    cluster_mass_t = ClusterMassTrue()
    assert isinstance(cluster_mass_t, ClusterMass)

    logM_args = cluster_mass_t.gen_bins_by_array(logM_bins)
    cluster_mass_t.update(parameters)

    return logM_args


@pytest.fixture(name="rich_args")
def fixture_cluster_mass_rich_args(parameters):
    """Fixture for cluster masses."""
    pivot_mass = 14.0
    pivot_redshift = 0.6
    proxy_bins = np.array([0.45805137, 0.81610273, 1.1741541, 1.53220547, 1.89025684])

    cluster_mass_r = ClusterMassRich(pivot_mass, pivot_redshift)
    assert isinstance(cluster_mass_r, ClusterMass)

    rich_args = cluster_mass_r.gen_bins_by_array(proxy_bins)
    cluster_mass_r.update(parameters)

    return rich_args


@pytest.fixture(name="cluster_abundance")
def fixture_cluster_abundance(parameters):
    """Fixture for cluster objects."""

    hmd_200 = ccl.halos.MassDef200c
    hmf_args: Dict[str, Any] = {}
    hmf_name = "Bocquet16"
    sky_area = 489

    cluster_abundance = ClusterAbundance(hmd_200, hmf_name, hmf_args, sky_area)
    assert isinstance(cluster_abundance, ClusterAbundance)

    cluster_abundance.update(parameters)

    return cluster_abundance


def test_initialize_objects(
    ccl_cosmo: ccl.Cosmology, cluster_abundance, z_args, logM_args, rich_args
):
    """Test initialization of cluster objects."""

    for z_arg in z_args:
        assert isinstance(z_arg, ClusterRedshiftArgument)

    for logM_arg in logM_args:
        assert isinstance(logM_arg, ClusterMassArgument)

    for rich_arg in rich_args:
        assert isinstance(rich_arg, ClusterMassArgument)

    assert isinstance(ccl_cosmo, ccl.Cosmology)
    assert isinstance(cluster_abundance, ClusterAbundance)


def test_cluster_mass_function_compute(
    ccl_cosmo: ccl.Cosmology, cluster_abundance, z_args, logM_args, rich_args
):
    """Test cluster mass function computations."""

    for redshift_arg, logM_arg, rich_arg in itertools.product(
        z_args, logM_args, rich_args
    ):
        assert math.isfinite(
            cluster_abundance.compute(ccl_cosmo, rich_arg, redshift_arg)
        )
        assert math.isfinite(
            cluster_abundance.compute(ccl_cosmo, logM_arg, redshift_arg)
        )
