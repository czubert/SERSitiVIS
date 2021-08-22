import numpy as np

def num_of_molecules(conc, vol):
    """
    Calculating number of particles contained in the solution.
    :param conc: Float, Must be in mol/dm**3
    :param vol: Float, Must be in ml
    :return: Float, Number of Molecules
    """
    n_av = 6.023 * 10 ** 23
    v_dm = vol * 10 ** (-3)
    
    return n_av * conc * v_dm


def cal_size_of_laser_spot(wave_length_nm, lens_numeric_aperture):
    """
    Calculating size of laser spot.
    :param lnm: Int, laser wavelength given in nm
    :param naa: Float, Lens parameter - Numerical aperture
    :return: Float, Size of laser spot in meters
    """
    wave_length_m = wave_length_nm * 10 ** (-9)  # changing nm to m as it is needed for formula
    return (1.22 * wave_length_m) / lens_numeric_aperture


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
