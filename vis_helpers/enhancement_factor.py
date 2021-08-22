import streamlit as st
from . import enhancement_factor_utils
from . import vis_utils


def main():
    st.header('Enhancement Factor calculator')
    
    # # #
    # # Solution Concentration
    #
    vis_utils.print_widget_labels('Sample concentration. x * 10^n mol/dm3. Please provide x and n:', 5, 0)
    cols = st.beta_columns(2)
    with cols[0]:
        x = st.number_input('Provide "x"', 1, 9, 1)
    with cols[1]:
        c = st.number_input('Provide "n"', -15, 0, -6)
    c = x * 10 ** (c)
    
    # # #
    # # Solution Volume
    #
    vis_utils.print_widget_labels('Volume of solution [ml]', 5, 0)
    v = st.number_input('', 0, 15, 2)
    
    # # #
    # # Laser wavelength
    #
    vis_utils.print_widget_labels('Laser wavelength [nm]', 5, 0)
    l_nm = st.number_input('', 450, 1200, 785)
    
    # # #
    # # Lens params
    #
    vis_utils.print_widget_labels('Lens parameter - Numerical aperture', 5, 0)
    na = st.number_input('', 0.0, 10.0, 0.40, 0.1)
    
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
    active_area = active_x * active_y * active_multi
    
    # # #
    # # Analyte coverage
    #
    vis_utils.print_widget_labels('The coverage of the analyte on the surface between 10^-6 and 6*10^-6 ~=10%', 5, 0)
    surface_coverage = st.number_input('', 0.0, 10.0, 0.40, 0.2)
    
    # # #
    # # Intensities
    #
    vis_utils.print_widget_labels('Intensity', 5, 0)
    cols = st.beta_columns(2)
    with cols[0]:
        i_raman = st.number_input('Raman Intensity', 0, 10000, 1000, 100)
    with cols[1]:
        i_sers = st.number_input('SERS Intensity', 0, 500000, 60000, 1000)
    
    st.write(enhancement_factor_utils.calculate_enhancement(
        c, v, l_nm, na, active_area, surface_coverage, i_sers, i_raman) / 1e+8)
