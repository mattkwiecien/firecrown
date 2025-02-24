"""
Tests for the perturbation theory systematics for both
Weak Lensing and Number Counts.
"""
import os

import pytest

import numpy as np
import pyccl as ccl
import pyccl.nl_pt as pt
import sacc

import firecrown.likelihood.gauss_family.statistic.source.weak_lensing as wl
import firecrown.likelihood.gauss_family.statistic.source.number_counts as nc
from firecrown.likelihood.gauss_family.statistic.two_point import TwoPoint
from firecrown.likelihood.gauss_family.gaussian import ConstGaussian
from firecrown.modeling_tools import ModelingTools
from firecrown.parameters import ParamsMap


@pytest.fixture(name="weak_lensing_source")
def fixture_weak_lensing_source():
    ia_systematic = wl.TattAlignmentSystematic()
    pzshift = wl.PhotoZShift(sacc_tracer="src0")
    return wl.WeakLensing(sacc_tracer="src0", systematics=[pzshift, ia_systematic])


@pytest.fixture(name="number_counts_source")
def fixture_number_counts_source():
    pzshift = nc.PhotoZShift(sacc_tracer="lens0")
    magnification = nc.ConstantMagnificationBiasSystematic(sacc_tracer="lens0")
    nl_bias = nc.PTNonLinearBiasSystematic(sacc_tracer="lens0")
    return nc.NumberCounts(
        sacc_tracer="lens0", has_rsd=True, systematics=[pzshift, magnification, nl_bias]
    )


@pytest.fixture(name="sacc_data")
def fixture_sacc_data():
    # Load sacc file
    # This shouldn't be necessary, since we only use the n(z) from the sacc file
    saccfile = os.path.join(
        os.path.split(__file__)[0],
        "../examples/des_y1_3x2pt/des_y1_3x2pt_sacc_data.fits",
    )
    return sacc.Sacc.load_fits(saccfile)


def test_pt_systematics(weak_lensing_source, number_counts_source, sacc_data):
    # The following disabling of pylint warnings are TEMPORARY. Disabling warnings is
    # generally not a good practice. In this case, the warnings are indicating that this
    # test is too complicated.
    #
    # pylint: disable-msg=too-many-locals
    # pylint: disable-msg=too-many-statements
    stats = [
        TwoPoint("galaxy_shear_xi_plus", weak_lensing_source, weak_lensing_source),
        TwoPoint("galaxy_shear_xi_minus", weak_lensing_source, weak_lensing_source),
        TwoPoint("galaxy_shearDensity_xi_t", number_counts_source, weak_lensing_source),
        TwoPoint("galaxy_density_xi", number_counts_source, number_counts_source),
    ]

    likelihood = ConstGaussian(statistics=stats)
    likelihood.read(sacc_data)
    src0_tracer = sacc_data.get_tracer("src0")
    lens0_tracer = sacc_data.get_tracer("lens0")
    z, nz = src0_tracer.z, src0_tracer.nz
    lens_z, lens_nz = lens0_tracer.z, lens0_tracer.nz

    # Define a ccl.Cosmology object using default parameters
    ccl_cosmo = ccl.CosmologyVanillaLCDM()
    ccl_cosmo.compute_nonlin_power()

    pt_calculator = pt.EulerianPTCalculator(
        with_NC=True,
        with_IA=True,
        log10k_min=-4,
        log10k_max=2,
        nk_per_decade=4,
        cosmo=ccl_cosmo,
    )
    modeling_tools = ModelingTools(pt_calculator=pt_calculator)
    modeling_tools.prepare(ccl_cosmo)

    # Bare CCL setup
    a_1 = 1.0
    a_2 = 0.5
    a_d = 0.5

    b_1 = 2.0
    b_2 = 1.0
    b_s = 1.0

    mag_bias = 1.0

    c_1, c_d, c_2 = pt.translate_IA_norm(
        ccl_cosmo, z=z, a1=a_1, a1delta=a_d, a2=a_2, Om_m2_for_c2=False
    )

    # Code that creates Pk2D objects:
    ptt_i = pt.PTIntrinsicAlignmentTracer(c1=(z, c_1), c2=(z, c_2), cdelta=(z, c_d))
    ptt_m = pt.PTMatterTracer()
    ptt_g = pt.PTNumberCountsTracer(b1=b_1, b2=b_2, bs=b_s)
    # IA
    pk_im = pt_calculator.get_biased_pk2d(tracer1=ptt_i, tracer2=ptt_m)
    pk_ii = pt_calculator.get_biased_pk2d(tracer1=ptt_i, tracer2=ptt_i)
    pk_gi = pt_calculator.get_biased_pk2d(tracer1=ptt_g, tracer2=ptt_i)
    # Galaxies
    pk_gm = pt_calculator.get_biased_pk2d(tracer1=ptt_g, tracer2=ptt_m)
    pk_gg = pt_calculator.get_biased_pk2d(tracer1=ptt_g, tracer2=ptt_g)

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

    # Make things faster by only using a couple of ells
    for s in likelihood.statistics:
        s.ell_for_xi = {"minimum": 2, "midpoint": 5, "maximum": 6e4, "n_log": 10}

    # Compute the log-likelihood, using the ccl.Cosmology object as the input
    _ = likelihood.compute_loglike(modeling_tools)

    # print(list(likelihood.statistics[0].cells.keys()))
    # pylint: disable=no-member
    ells = likelihood.statistics[0].ells
    cells_GG = likelihood.statistics[0].cells[("shear", "shear")]
    cells_GI = likelihood.statistics[0].cells[("shear", "intrinsic_pt")]
    cells_II = likelihood.statistics[0].cells[("intrinsic_pt", "intrinsic_pt")]
    cells_cs_total = likelihood.statistics[0].cells["total"]

    # print(list(likelihood.statistics[2].cells.keys()))
    cells_gG = likelihood.statistics[2].cells[("galaxies", "shear")]
    cells_gI = likelihood.statistics[2].cells[("galaxies", "intrinsic_pt")]
    cells_mI = likelihood.statistics[2].cells[("magnification+rsd", "intrinsic_pt")]

    # print(list(likelihood.statistics[3].cells.keys()))
    cells_gg = likelihood.statistics[3].cells[("galaxies", "galaxies")]
    cells_gm = likelihood.statistics[3].cells[("galaxies", "magnification+rsd")]
    cells_mm = likelihood.statistics[3].cells[
        ("magnification+rsd", "magnification+rsd")
    ]
    cells_gg_total = likelihood.statistics[3].cells["total"]
    # pylint: enable=no-member
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
    cl_mm = ccl.angular_cl(ccl_cosmo, t_m, t_m, ells)

    cl_cs_theory = cl_GG + 2 * cl_GI + cl_II
    cl_gg_theory = cl_gg + 2 * cl_gm + cl_mm

    assert np.allclose(cl_GG, cells_GG, atol=0, rtol=1e-7)
    assert np.allclose(cl_GI, cells_GI, atol=0, rtol=1e-7)
    assert np.allclose(cl_II, cells_II, atol=0, rtol=1e-7)
    assert np.allclose(cl_gG, cells_gG, atol=0, rtol=1e-7)
    assert np.allclose(cl_gI, cells_gI, atol=0, rtol=1e-7)
    assert np.allclose(cl_gg, cells_gg, atol=0, rtol=1e-7)
    assert np.allclose(cl_mI, cells_mI, atol=0, rtol=1e-7)
    assert np.allclose(cl_gm, cells_gm, atol=0, rtol=1e-7)
    assert np.allclose(cl_mm, cells_mm, atol=0, rtol=1e-7)
    assert np.allclose(cl_cs_theory, cells_cs_total, atol=0, rtol=1e-7)
    assert np.allclose(cl_gg_theory, cells_gg_total, atol=0, rtol=1e-7)


def test_pt_mixed_systematics(sacc_data):
    # The following disabling of pylint warnings are TEMPORARY. Disabling warnings is
    # generally not a good practice. In this case, the warnings are indicating that this
    # test is too complicated.
    #
    # pylint: disable-msg=too-many-locals

    ia_systematic = wl.TattAlignmentSystematic()
    wl_source = wl.WeakLensing(sacc_tracer="src0", systematics=[ia_systematic])

    magnification = nc.ConstantMagnificationBiasSystematic(sacc_tracer="lens0")
    nc_source = nc.NumberCounts(
        sacc_tracer="lens0", has_rsd=True, systematics=[magnification]
    )

    stat = TwoPoint(
        source0=nc_source,
        source1=wl_source,
        sacc_data_type="galaxy_shearDensity_xi_t",
    )

    # Create the likelihood from the statistics
    likelihood = ConstGaussian(statistics=[stat])
    likelihood.read(sacc_data)

    src0_tracer = sacc_data.get_tracer("src0")
    lens0_tracer = sacc_data.get_tracer("lens0")
    z, nz = src0_tracer.z, src0_tracer.nz
    lens_z, lens_nz = lens0_tracer.z, lens0_tracer.nz

    # Define a ccl.Cosmology object using default parameters
    ccl_cosmo = ccl.CosmologyVanillaLCDM()
    ccl_cosmo.compute_nonlin_power()

    pt_calculator = pt.EulerianPTCalculator(
        with_NC=True,
        with_IA=True,
        log10k_min=-4,
        log10k_max=2,
        nk_per_decade=4,
        cosmo=ccl_cosmo,
    )
    modeling_tools = ModelingTools(pt_calculator=pt_calculator)
    modeling_tools.prepare(ccl_cosmo)

    # Bare CCL setup
    a_1 = 1.0
    a_2 = 0.5
    a_d = 0.5

    bias = 2.0
    mag_bias = 1.0

    c_1, c_d, c_2 = pt.translate_IA_norm(
        ccl_cosmo, z=z, a1=a_1, a1delta=a_d, a2=a_2, Om_m2_for_c2=False
    )

    # Code that creates Pk2D objects:
    ptt_i = pt.PTIntrinsicAlignmentTracer(c1=(z, c_1), c2=(z, c_2), cdelta=(z, c_d))
    ptt_m = pt.PTMatterTracer()
    # IA
    pk_mi = pt_calculator.get_biased_pk2d(tracer1=ptt_m, tracer2=ptt_i)

    # Set the parameters for our systematics
    systematics_params = ParamsMap(
        {
            "ia_a_1": a_1,
            "ia_a_2": a_2,
            "ia_a_d": a_d,
            "lens0_bias": bias,
            "lens0_mag_bias": mag_bias,
        }
    )

    # Apply the systematics parameters
    likelihood.update(systematics_params)

    # Make things faster by only using a couple of ells
    for s in likelihood.statistics:
        s.ell_for_xi = {"minimum": 2, "midpoint": 5, "maximum": 6e4, "n_log": 10}

    # Compute the log-likelihood, using the ccl.Cosmology object as the input
    _ = likelihood.compute_loglike(modeling_tools)

    # print(list(likelihood.statistics[0].cells.keys()))
    # pylint: disable=no-member

    ells = likelihood.statistics[0].ells

    # print(list(likelihood.statistics[2].cells.keys()))
    cells_gG = likelihood.statistics[0].cells[("galaxies+magnification+rsd", "shear")]
    cells_gI = likelihood.statistics[0].cells[
        ("galaxies+magnification+rsd", "intrinsic_pt")
    ]
    # pylint: enable=no-member

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
        has_rsd=True,
        dndz=(lens_z, lens_nz),
        bias=(lens_z, bias * np.ones_like(lens_z)),
        mag_bias=(lens_z, mag_bias * np.ones_like(lens_z)),
    )

    # Galaxies
    cl_gG = ccl.angular_cl(ccl_cosmo, t_g, t_lens, ells)
    cl_gI = ccl.angular_cl(ccl_cosmo, t_g, t_ia, ells, p_of_k_a=pk_mi)

    assert np.allclose(cl_gG, cells_gG, atol=0, rtol=1e-7)
    assert np.allclose(cl_gI, cells_gI, atol=0, rtol=1e-7)
