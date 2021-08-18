import numpy as np


def calculate_enhancement(c, v, l_nm, na, active_area, surface_coverage, i_sers, i_raman):
    """
    Looking for parameters to formula:
    EF = (Isers/Nsers) * (Nraman/Iraman)
    :param c: Float, Concentration of analyte in solution (in mol/dm^3)
    :param v: Int, Volume of solution (ml)
    :param l_nm: Int, Laser wavelength in nm
    :param na: Float, Lens parameter - Numerical aperture
    :param active_area: Int, The area of active surface of the SERS substrate
    :param surface_coverage: Float, the coverage of the analyte on the surface between 10^-6 and 6*10^-6 ~=10%
    :return: Float, Enhancement Factor
    """
    num_molecules = num_of_molecules(c, v)
    s_laser = cal_size_of_laser_spot(l_nm, na)
    s0 = cal_laser_spot_surface_area(s_laser)
    
    # needed directly to calculate EF
    n_sers = cal_n_sers(active_area, s0, num_molecules, surface_coverage)
    n_raman = cal_n_raman(s0)
    
    return (i_sers / n_sers) * (n_raman / i_raman)


def num_of_molecules(conc, vol):
    """
    Calculating number of particles contained in the solution.
    Returns number of molecules in the solution
    :argument conc: Must be in mol/dm**3
    :argument vol: Must be in ml
    :param conc: Float
    :param vol: Float
    :return: Float, Number of Molecules
    """
    n_av = 6.023 * 10 ** 23
    v_dm = vol * 10 ** (-3)
    
    return n_av * conc * v_dm


def cal_size_of_laser_spot(lnm, naa):
    """
    Calculating size of laser spot.
    Returns size in meters.
    :argument lnm: laser wavelength given in nm
    :argument naa: numerical aperture value
    :param lnm: Int, Length in meters
    :param naa: Float, Lens parameter - Numerical aperture
    :return: Float, Size of laser spot
    """
    lm = lnm * 10 ** (-9)  # changing nm to m as it is needed for formula
    return (1.22 * lm) / naa


def cal_laser_spot_surface_area(size_laser_spot):
    """
    Calculating laser spot surface area based on the diameter of the laser spot.
    :param size_laser_spot: Float, Laser spot diameter
    :return: Float, Laser spot surface area
    """
    return np.pi * (size_laser_spot / 2) ** 2


def cal_n_sers(active_area, s0, num_of_molecules, surface_coverage):
    # TODO make the variables adjustable
    
    s_pmba = 2e-19 * num_of_molecules
    
    s_substrate = active_area * 1e-6
    
    n_laser = num_of_molecules / (s_substrate / s0)
    
    return n_laser * surface_coverage


def cal_n_raman(s0):
    # TODO make it possible to add different compounds not only PMBA
    
    # Vpmba = S0 * h
    v_pmba = s0 * 2e-3
    
    # calculating mass in the volume of cristal
    m = v_pmba * 1.3e+6
    
    # calculating num of moles m/M
    n = m / 154.19
    
    return n * 6.02e+23
