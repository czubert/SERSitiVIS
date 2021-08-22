import streamlit as st
from . import vis_utils


def get_concentration():
    # # #
    # # Solution Concentration
    #
    vis_utils.print_widget_labels('Sample concentration. x * 10^n mol/dm3. Please provide x and n:', 5, 0)
    cols = st.beta_columns(2)
    with cols[0]:
        multiplier = st.number_input('Provide "x"', 1, 9, 1)
    with cols[1]:
        exponent = st.number_input('Provide "n"', -15, 0, -6)
    return multiplier * 10 ** (exponent)


def get_volume():
    # # #
    # # Solution Volume
    #
    vis_utils.print_widget_labels('Volume of solution [ml]', 5, 0)
    return st.number_input('', 0, 15, 2)


def get_Laser_wave_length():
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
    return st.number_input('', 0.0, 10.0, 0.40, 0.1)


def get_active_surface_area():
    # # #
    # # Active surface
    #
    vis_utils.print_widget_labels('The area of active surface of the SERS substrate [mm]', 5, 0)
    cols = st.beta_columns(3)
    with cols[0]:
        active_x = st.number_input('', 0.0, 50.0, 5.0, 0.1)
    with cols[1]:
        active_y = st.number_input('', 0.0, 50.0, 4.0, 0.1)
    with cols[2]:
        active_multi = st.number_input('', 0.0, 10.0, 2.0, 0.05)
    return active_x * active_y * active_multi


def get_surface_coverage():
    # # #
    # # Surface Coverage
    #
    vis_utils.print_widget_labels('The coverage of the analyte on the surface. x * 10^n. Please provide x and n:', 5, 0)
    cols = st.beta_columns(2)
    with cols[0]:
        multiplier = st.number_input('Provide "x"', 1, 9, 1, key='coverage')
    with cols[1]:
        exponent = st.number_input('Provide "n"', -15, 0, -6, key='coverage')
    # return multiplier * 10 ** (exponent)
    
    return 0.1  # TODO checking if it works


def get_laser_intensities():
    # # #
    # # Intensities
    #
    vis_utils.print_widget_labels('Intensity', 5, 0)
    cols = st.beta_columns(2)
    with cols[0]:
        i_raman = st.number_input('Raman Intensity', 0, 10000, 1000, 100)
    with cols[1]:
        i_sers = st.number_input('SERS Intensity', 0, 500000, 60000, 1000)
    return i_raman, i_sers


def get_molecular_weight():
    vis_utils.print_widget_labels('Provide molecular weight', 5, 0)
    return st.number_input('', 0.0, 1000.0, 154.19, 0.01)
