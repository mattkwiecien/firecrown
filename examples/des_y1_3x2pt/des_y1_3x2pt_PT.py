#!/usr/bin/env python

"""Example factory function for DES Y1 3x2pt likelihood."""

import os

from typing import Dict, Union, Tuple

import sacc
import pyccl as ccl
import pyccl.nl_pt

import firecrown.likelihood.gauss_family.statistic.source.weak_lensing as wl
import firecrown.likelihood.gauss_family.statistic.source.number_counts as nc
from firecrown.likelihood.gauss_family.statistic.two_point import TwoPoint
from firecrown.likelihood.gauss_family.gaussian import ConstGaussian
from firecrown.parameters import ParamsMap
from firecrown.modeling_tools import ModelingTools
from firecrown.likelihood.likelihood import Likelihood


saccfile = os.path.expanduser(
    os.path.expandvars(
        "${FIRECROWN_DIR}/examples/des_y1_3x2pt/des_y1_3x2pt_sacc_data.fits"
    )
)


def build_likelihood(_) -> Tuple[Likelihood, ModelingTools]:
    """Likelihood factory function for DES Y1 3x2pt analysis."""

    # Load sacc file
    sacc_data = sacc.Sacc.load_fits(saccfile)

    # Define sources
    sources: Dict[str, Union[wl.WeakLensing, nc.NumberCounts]] = {}

    # Define the intrinsic alignment systematic. This will be added to the
    # lensing sources later
    ia_systematic = wl.TattAlignmentSystematic()

    # Define the photo-z shift systematic.
    src_pzshift = wl.PhotoZShift(sacc_tracer="src0")

    # Create the weak lensing source, specifying the name of the tracer in the
    # sacc file and a list of systematics
    sources["src0"] = wl.WeakLensing(
        sacc_tracer="src0", systematics=[src_pzshift, ia_systematic]
    )

    lens_pzshift = nc.PhotoZShift(sacc_tracer="lens0")
    magnification = nc.ConstantMagnificationBiasSystematic(sacc_tracer="lens0")
    nl_bias = nc.PTNonLinearBiasSystematic(sacc_tracer="lens0")
    sources["lens0"] = nc.NumberCounts(
        sacc_tracer="lens0",
        has_rsd=True,
        systematics=[lens_pzshift, magnification, nl_bias],
    )

    # Define the statistics we like to include in the likelihood
    # The only place the dict 'stats' gets used, other than setting values in
    # it, is to call 'values' on it. Thus we don't need a dict, we need a list
    # of the values. The keys assigned to the dict are never used.
    stats = {}
    for stat, sacc_stat in [
        ("xip", "galaxy_shear_xi_plus"),
        ("xim", "galaxy_shear_xi_minus"),
    ]:
        # Define two-point statistics, given two sources (from above) and
        # the type of statistic.
        stats[f"{stat}_src0_src0"] = TwoPoint(
            source0=sources["src0"],
            source1=sources["src0"],
            sacc_data_type=sacc_stat,
        )
    stats["gammat_lens0_src0"] = TwoPoint(
        source0=sources["lens0"],
        source1=sources["src0"],
        sacc_data_type="galaxy_shearDensity_xi_t",
    )

    stats["wtheta_lens0_lens0"] = TwoPoint(
        source0=sources["lens0"],
        source1=sources["lens0"],
        sacc_data_type="galaxy_density_xi",
    )

    # Create the likelihood from the statistics
    pt_calculator = pyccl.nl_pt.EulerianPTCalculator(
        with_NC=True,
        with_IA=True,
        log10k_min=-4,
        log10k_max=2,
        nk_per_decade=20,
    )

    modeling_tools = ModelingTools(pt_calculator=pt_calculator)
    likelihood = ConstGaussian(statistics=list(stats.values()))

    # Read the two-point data from the sacc file
    likelihood.read(sacc_data)

    # an object called "likelihood" must be defined
    print(
        "Using parameters:", list(likelihood.required_parameters().get_params_names())
    )

    # To allow this likelihood to be used in cobaya or cosmosis,
    # return the likelihood object
    return likelihood, modeling_tools


# We can also run the likelihood directly
def run_likelihood() -> None:
    """Produce some plots using the likelihood function built by
    :python:`build_likelihood`.
    """
    # We do imports here to save a bit of time when importing this module but
    # not using the run_likelihood function.
    # pylint: disable=import-outside-toplevel
    import numpy as np
    import matplotlib.pyplot as plt

    # pylint: enable=import-outside-toplevel

    likelihood, tools = build_likelihood(None)

    # Load sacc file
    sacc_data = sacc.Sacc.load_fits(saccfile)

    src0_tracer = sacc_data.get_tracer("src0")
    lens0_tracer = sacc_data.get_tracer("lens0")
    z, nz = src0_tracer.z, src0_tracer.nz
    lens_z, lens_nz = lens0_tracer.z, lens0_tracer.nz

    # Define a ccl.Cosmology object using default parameters
    ccl_cosmo = ccl.CosmologyVanillaLCDM()
    ccl_cosmo.compute_nonlin_power()

    # Bare CCL setup
    a_1 = 1.0
    a_2 = 0.5
    a_d = 0.5

    b_1 = 2.0
    b_2 = 1.0
    b_s = 1.0

    mag_bias = 1.0

    c_1, c_d, c_2 = pyccl.nl_pt.translate_IA_norm(
        ccl_cosmo, z=z, a1=a_1, a1delta=a_d, a2=a_2, Om_m2_for_c2=False
    )

    # Code that creates a Pk2D object:
    ptc = pyccl.nl_pt.EulerianPTCalculator(
        with_NC=True,
        with_IA=True,
        log10k_min=-4,
        log10k_max=2,
        nk_per_decade=20,
        cosmo=ccl_cosmo,
    )
    ptt_i = pyccl.nl_pt.PTIntrinsicAlignmentTracer(
        c1=(z, c_1), c2=(z, c_2), cdelta=(z, c_d)
    )
    ptt_m = pyccl.nl_pt.PTMatterTracer()
    ptt_g = pyccl.nl_pt.PTNumberCountsTracer(b1=b_1, b2=b_2, bs=b_s)
    # IA
    pk_im = ptc.get_biased_pk2d(ccl_cosmo, ptt_i, tracer2=ptt_m)
    pk_ii = ptc.get_biased_pk2d(ccl_cosmo, tracer1=ptt_i, tracer2=ptt_i)
    pk_gi = ptc.get_biased_pk2d(ccl_cosmo, tracer1=ptt_g, tracer2=ptt_i)
    # Galaxies
    pk_gm = ptc.get_biased_pk2d(ccl_cosmo, tracer1=ptt_g, tracer2=ptt_m)
    pk_gg = ptc.get_biased_pk2d(ccl_cosmo, tracer1=ptt_g, tracer2=ptt_g)
    # Magnification: just a matter-matter P(k)
    pk_mm = ptc.get_biased_pk2d(ccl_cosmo, tracer1=ptt_m, tracer2=ptt_m)

    # Set the parameters for our systematics
    systematics_params = ParamsMap(
        {
            "ia_a_1": a_1,
            "ia_a_2": a_2,
            "ia_a_d": a_d,
            "lens0_bias": b_1,
            "lens0_b_2": b_2,
            "lens0_b_s": b_s,
            "lens0_mag_bias": mag_bias,
            "src0_delta_z": 0.000,
            "lens0_delta_z": 0.000,
        }
    )

    # Apply the systematics parameters
    likelihood.update(systematics_params)

    # Prepare the cosmology object
    tools.prepare(ccl_cosmo)

    # Compute the log-likelihood, using the ccl.Cosmology object as the input
    log_like = likelihood.compute_loglike(tools)

    print(f"Log-like = {log_like:.1f}")

    # Plot the predicted and measured statistic
    # x = likelihood.statistics[0].ell_or_theta_
    # y_data = likelihood.statistics[0].measured_statistic_

    assert isinstance(likelihood, ConstGaussian)
    assert likelihood.cov is not None

    # y_err = np.sqrt(np.diag(likelihood.cov))[: len(x)]
    # y_theory = likelihood.statistics[0].predicted_statistic_

    print(list(likelihood.statistics[0].cells.keys()))

    ells = likelihood.statistics[0].ells
    cells_GG = likelihood.statistics[0].cells[("shear", "shear")]
    cells_GI = likelihood.statistics[0].cells[("shear", "intrinsic_pt")]
    cells_II = likelihood.statistics[0].cells[("intrinsic_pt", "intrinsic_pt")]
    cells_cs_total = likelihood.statistics[0].cells["total"]

    print(list(likelihood.statistics[2].cells.keys()))
    cells_gG = likelihood.statistics[2].cells[("galaxies", "shear")]
    cells_gI = likelihood.statistics[2].cells[("galaxies", "intrinsic_pt")]
    cells_mI = likelihood.statistics[2].cells[("magnification+rsd", "intrinsic_pt")]

    print(list(likelihood.statistics[3].cells.keys()))
    cells_gg = likelihood.statistics[3].cells[("galaxies", "galaxies")]
    cells_gm = likelihood.statistics[3].cells[("galaxies", "magnification+rsd")]
    cells_gg_total = likelihood.statistics[3].cells["total"]

    # Code that computes effect from IA using that Pk2D object
    t_lens = ccl.WeakLensingTracer(ccl_cosmo, dndz=(z, nz))
    t_ia = ccl.WeakLensingTracer(
        ccl_cosmo,
        dndz=(z, nz),
        has_shear=False,
        ia_bias=(z, np.ones_like(z)),
        use_A_ia=False,
    )
    t_g = ccl.NumberCountsTracer(
        ccl_cosmo,
        has_rsd=False,
        dndz=(lens_z, lens_nz),
        bias=(lens_z, np.ones_like(lens_z)),
    )
    t_m = ccl.NumberCountsTracer(
        ccl_cosmo,
        has_rsd=True,
        dndz=(lens_z, lens_nz),
        bias=None,
        mag_bias=(lens_z, mag_bias * np.ones_like(lens_z)),
    )
    cl_GI = ccl.angular_cl(ccl_cosmo, t_lens, t_ia, ells, p_of_k_a=pk_im)
    cl_II = ccl.angular_cl(ccl_cosmo, t_ia, t_ia, ells, p_of_k_a=pk_ii)
    # The weak gravitational lensing power spectrum
    cl_GG = ccl.angular_cl(ccl_cosmo, t_lens, t_lens, ells)

    # Galaxies
    cl_gG = ccl.angular_cl(ccl_cosmo, t_g, t_lens, ells, p_of_k_a=pk_gm)
    cl_gI = ccl.angular_cl(ccl_cosmo, t_g, t_ia, ells, p_of_k_a=pk_gi)
    cl_gg = ccl.angular_cl(ccl_cosmo, t_g, t_g, ells, p_of_k_a=pk_gg)
    # Magnification
    cl_mI = ccl.angular_cl(ccl_cosmo, t_m, t_ia, ells, p_of_k_a=pk_im)
    cl_gm = ccl.angular_cl(ccl_cosmo, t_g, t_m, ells, p_of_k_a=pk_gm)
    cl_mm = ccl.angular_cl(ccl_cosmo, t_m, t_m, ells, p_of_k_a=pk_mm)

    # The observed angular power spectrum is the sum of the two.
    cl_cs_theory = cl_GG + 2 * cl_GI + cl_II
    cl_gg_theory = cl_gg + 2 * cl_gm + cl_mm

    fig, ax = plt.subplots(2, 1, sharex=True, figsize=(6, 6))
    fig.subplots_adjust(hspace=0)
    # ax[0].plot(x, y_theory, label="Total")
    ax[0].plot(ells, cells_GG, label="GG firecrown")
    ax[0].plot(ells, cl_GG, ls="--", label="GG CCL")
    ax[0].plot(ells, -cells_GI, label="-GI firecrown")
    ax[0].plot(ells, -cl_GI, ls="--", label="-GI CCL")
    ax[0].plot(ells, cells_II, label="II firecrown")
    ax[0].plot(ells, cl_II, ls="--", label="II CCL")
    ax[0].plot(ells, -cells_gI, label="-Ig firecrown")
    ax[0].plot(ells, -cl_gI, ls="--", label="-Ig CCL")
    ax[0].plot(ells, cells_cs_total, label="total CS firecrown")
    ax[0].plot(ells, cl_cs_theory, ls="--", label="total CS CCL")

    ax[1].plot(ells, cells_gG, label="Gg firecrown")
    ax[1].plot(ells, cl_gG, ls="--", label="Gg CCL")
    ax[1].plot(ells, cells_gg, label="gg firecrown")
    ax[1].plot(ells, cl_gg, ls="--", label="gg CCL")
    ax[1].plot(ells, -cells_mI, label="-mI firecrown")
    ax[1].plot(ells, -cl_mI, ls="--", label="-mI CCL")
    ax[1].plot(ells, cells_gm, label="gm firecrown")
    ax[1].plot(ells, cl_gm, ls="--", label="gm CCL")
    ax[1].plot(ells, cells_gg_total, label="total gg firecrown")
    ax[1].plot(ells, cl_gg_theory, ls="--", label="total gg CCL")

    # ax[0].errorbar(x, y_data, y_err, ls="none", marker="o")
    ax[0].set_xscale("log")
    ax[1].set_xlabel(r"$\ell$")
    ax[1].set_ylabel(r"$C_\ell$")
    for a in ax:
        a.set_yscale("log")
        a.set_ylabel(r"$C_\ell$")
        a.legend(fontsize="small")

    fig.suptitle("PT Cls, including IA, galaxy bias, magnification")
    fig.savefig("pt_cls.png", facecolor="white", dpi=300)

    plt.show()


if __name__ == "__main__":
    run_likelihood()
