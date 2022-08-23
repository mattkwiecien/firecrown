"""CosmoSIS Likelihood Connector

This module provides the class FirecrownLikelihood, and the hook functions
for this module to be a CosmoSIS likelihood module.

Note that the class FirecrownLikelihood does *not* inherit from firecrown's
likelihood abstract base class; it the implementation of a CosmoSIS module,
not a specific likelihood.
"""

from typing import Dict

import cosmosis.datablock
from cosmosis.datablock import option_section
from cosmosis.datablock import names as section_names
import pyccl as ccl
from firecrown.connector.mapping import mapping_builder, MappingCosmoSIS
from firecrown.likelihood.gauss_family.statistic.two_point import TwoPoint
from firecrown.likelihood.likelihood import load_likelihood, Likelihood
from firecrown.parameters import ParamsMap


def extract_section(sample: cosmosis.datablock, section: str) -> Dict:
    """Extract the all the parameters from the name datablock section into a
    dictionary."""
    sec_dict = {name: sample[section, name] for _, name in sample.keys(section=section)}
    return sec_dict


class FirecrownLikelihood:
    """CosmoSIS likelihood module for calculating Firecrown likelihood.

    In this simplest implementation, we have only a single module. This module
    is responsible for calling CCL to perform theory calculations, based on the
    output of CAMB, and also for calculating the data likelihood baesd on this
    theory.

    :param config: current CosmoSIS datablock
    """

    likelihood: Likelihood
    map: MappingCosmoSIS

    def __init__(self, config: cosmosis.datablock):
        """Create the FirecrownLikelihood object from the given configuration."""
        likelihood_source = config.get_string(option_section, "likelihood_source", "")
        if likelihood_source == "":
            likelihood_source = config[option_section, "firecrown_config"]

        require_nonlinear_pk = config.get_bool(
            option_section, "require_nonlinear_pk", False
        )

        self.likelihood = load_likelihood(likelihood_source)
        self.map = mapping_builder(
            input_style="CosmoSIS", require_nonlinear_pk=require_nonlinear_pk
        )

    def execute(self, sample: cosmosis.datablock):
        """This is the method called for each sample generated by the sampler."""

        cosmological_params = extract_section(sample, "cosmological_parameters")
        self.map.set_params_from_cosmosis(cosmological_params)

        ccl_args = self.map.calculate_ccl_args(sample)

        cosmo = ccl.CosmologyCalculator(**self.map.asdict(), **ccl_args)

        # TODO: Future development will need to capture elements that get put into the
        # datablock. This probably will be in a different "physics module" and not in
        # the likelihood module. And it requires updates to Firecrown to split the
        # calculations. e.g., data_vector/firecrown_theory  data_vector/firecrown_data

        firecrown_params = self.calculate_firecrown_params(sample)

        self.likelihood.update(firecrown_params)
        lnlike = self.likelihood.compute_loglike(cosmo)

        sample.put_double(section_names.likelihoods, "firecrown_like", lnlike)

        # Save concatenated data vector and inverse covariance to enable support
        # for the CosmoSIS fisher sampler.
        sample.put(
            "data_vector", "firecrown_theory", self.likelihood.predicted_data_vector
        )
        sample.put(
            "data_vector", "firecrown_data", self.likelihood.measured_data_vector
        )
        sample.put(
            "data_vector", "firecrown_inverse_covariance", self.likelihood.inv_cov
        )

        # Write out theory and data vectors to the data block the ease debugging.
        for stat in self.likelihood.statistics:
            if isinstance(stat, TwoPoint):
                tracer = f"{stat.sacc_tracers[0]}_{stat.sacc_tracers[1]}"

                sample.put(
                    "data_vector",
                    f"ell_or_theta_{stat.sacc_data_type}_{tracer}",
                    stat.ell_or_theta_,
                )
                sample.put(
                    "data_vector",
                    f"theory_{stat.sacc_data_type}_{tracer}",
                    stat.predicted_statistic_,
                )
                sample.put(
                    "data_vector",
                    f"data_{stat.sacc_data_type}_{tracer}",
                    stat.measured_statistic_,
                )

        return 0

    def calculate_firecrown_params(self, sample: cosmosis.datablock) -> ParamsMap:
        """Calculate the ParamsMap for this sample."""
        firecrown_params = ParamsMap()
        for section in sample.sections():
            if "firecrown" in section:
                sec_dict = extract_section(sample, section)
                firecrown_params = ParamsMap({**firecrown_params, **sec_dict})
        return firecrown_params


def setup(config: cosmosis.datablock) -> FirecrownLikelihood:
    """Setup hoook for a CosmoSIS module. Returns an instance of
    class FirecrownLikelihood. The same object will be passed to the CosmoSIS
    execute hook."""
    return FirecrownLikelihood(config)


def execute(sample: cosmosis.datablock, instance: FirecrownLikelihood) -> int:
    """Execute hook for a CosmoSIS module. Return 0 on success. The parameter
    `sample` represents the current MCMC sample; `instance` is the
    FirecrownLikelihood object created by `setup`."""
    return instance.execute(sample)


def cleanup(_):
    """Cleanup hook for a CosmoSIS module. This one has nothing to do."""
    return 0
