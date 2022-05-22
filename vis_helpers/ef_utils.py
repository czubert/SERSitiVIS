import streamlit as st
from . import vis_utils


def get_concentration():
    # # #
    # # Solution Concentration
    #
    st.markdown(
        r'### <p style="font-weight:500; margin-top:{5}px;margin-bottom:{0}px">Sample concentration. '
        r'$$x * 10^n \frac{mol}{dm^3}$$. Please provide x and n:</p>',
        unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        multiplier = st.number_input('Provide "x"', 1, 9, 1)
    with cols[1]:
        exponent = st.number_input('Provide "n"', -15, 0, -6)
    return multiplier * 10 ** (exponent)


def get_volume():
    # # #
    # # Solution Volume
    #
    vis_utils.print_widget_labels('Volume of solution [ul]', 5, 0)
    return st.number_input('', 0.0, 10000.0, 2000.0, 10.0) / 1000


def get_laser_wave_length():
    # # #
    # # Laser wavelength
    #
    vis_utils.print_widget_labels('Laser wavelength [nm]', 5, 0)
    return st.number_input('', 450, 1200, 785)


def get_lens_params():
    # # #
    # # Lens params
    #
    vis_utils.print_widget_labels('Lens parameter - Numerical Aperture (NA)', 5, 0)
    return st.number_input('', 0.0, 10.0, 0.22, 0.01)


def get_active_surface_area():
    # # #
    # # Active surface
    #
    vis_utils.print_widget_labels('The area of active surface of the SERS substrate [mm]', 5, 0)
    cols = st.columns(3)
    with cols[0]:
        active_x = st.number_input('First dimension (x)', 0.0, 50.0, 5.0, 0.1)
    with cols[1]:
        active_y = st.number_input('Second dimension (y)', 0.0, 50.0, 4.0, 0.1)
    with cols[2]:
        dev_coeff = st.number_input('Surface area development coefficient', 0.0, 10.0, 2.0, 0.05)

    return (active_x * active_y * 10 ** (-6)) * dev_coeff


def get_surface_coverage():
    # # #
    # # Surface Coverage
    #
    vis_utils.print_widget_labels('The coverage of the surface by the analyte', 5, 0)
    return st.number_input('', 0.0, 1.0, 0.1, 0.05, key='coverage')


def get_laser_intensities():
    # # #
    # # Intensities
    #
    vis_utils.print_widget_labels('Intensity', 5, 0)
    cols = st.columns(2)
    with cols[0]:
        i_raman = st.number_input('Raman Intensity', 1, 10000, 1000, 100)
    with cols[1]:
        i_sers = st.number_input('SERS Intensity', 1, 500000, 60000, 1000)
    return i_sers, i_raman


def get_molecular_weight():
    vis_utils.print_widget_labels('Provide molecular weight', 5, 0)
    return st.number_input('', 0.001, 1000.0, 154.19, 0.01)


def get_compound_density():
    vis_utils.print_widget_labels('Provide compound density', 5, 0)
    return st.number_input('', 0.001, 20.0, 1.3, 0.1)


def get_penetration_depth():
    vis_utils.print_widget_labels(
        'Provide depth into which the laser penetrates the chemical compound in crystalline form [mm]', 5, 0)
    penetration_depth = st.number_input('', 0.0, 10.0, 2.0, 0.1)
    return penetration_depth * 10 ** (-3)  # mm -> m


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


def cal_n_raman(v_compound, compound_density, compound_molecular_weight):
    """
    Calculating the number of molecules of the irradiated crystal
    :param v_compound: The volume of your chemical compound crystal subjected to laser illumination [m^3]
    :param compound_density:density of the chemical compound g/cm^3
    :param compound_molecular_weight: Mass of the irradiated crystal [g]
    :return: Float, N_Raman - number of molecules of the irradiated crystal
    """
    # calculating the mass of the irradiated crystal [g]
    m = v_compound * (compound_density * 10 ** 6)
    # calculating the number of moles of the irradiated crystal [mol]
    n = m / compound_molecular_weight
    
    # mol * 1/mol
    return n * 6.02e+23  # calculating the number of molecules using the Avogadro constant
