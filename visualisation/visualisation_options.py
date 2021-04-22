import streamlit as st

SINGLE = 'Single spectra'
MS = "Mean spectrum"
GS = "Grouped spectra"
P3D = "Plot 3D"


def bwtek_vis_options():
    """
    Different types of BWTek data visualisation
    :param df: DataFrame
    :param plots_color: list
    :param template: str
    """
    # showing sidebar
    chart_type = st.sidebar.radio(
        'Choose type of chart',
        (SINGLE, MS, GS, P3D), index=0)
    
    st.header(chart_type)
    # show_plot(df, plots_color, template, display_opt=chart_type)
    return chart_type


def vis_options(spectrometer):
    options = [SINGLE, GS]
    
    if spectrometer == 'BWTEK':
        options = [SINGLE, MS, GS, P3D]
    
    st.sidebar.write('#### Choose type of chart', unsafe_allow_html=True)
    chart_type = st.sidebar.radio(
        '',
        (options), 0)
    
    st.header(chart_type)
    return chart_type
