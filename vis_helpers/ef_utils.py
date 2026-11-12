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
    return st.number_input('Volume of solution [µl]', 0.0, 10000.0, 2000.0, 10.0) / 1000


def get_laser_wave_length():
    # # #
    # # Laser wavelength
    #
    return st.number_input('Laser wavelength [nm]', 450, 1200, 785)


def get_lens_params():
    # # #
    # # Lens params
    #
    return st.number_input('Lens parameter - Numerical Aperture (NA)', 0.0, 10.0, 0.22, 0.01)


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
    return st.number_input('The coverage of the surface by the analyte (0-1)', 0.0, 1.0, 0.1, 0.05, key='coverage')


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
    return st.number_input('Molecular weight [g/mol]', 0.001, 1000.0, 154.19, 0.01)


def get_compound_density():
    return st.number_input('Compound density [g/cm³]', 0.001, 20.0, 1.3, 0.1)


def get_penetration_depth():
    penetration_depth = st.number_input(
        'Depth into which the laser penetrates the chemical compound in crystalline form [mm]', 0.0, 10.0, 2.0, 0.1)
    return penetration_depth * 10 ** (-3)  # mm -> m
