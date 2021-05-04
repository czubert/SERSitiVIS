import streamlit as st

SINGLE = 'Single spectra'
MS = "Mean spectrum"
GS = "Grouped spectra"
P3D = "Plot 3D"

RAW = "Raw Data"
OPT = "Optimised Data"
NORM = "Normalized"


def vis_options(spectrometer):
    """
    Different types of visualisation for other data types
    :param spectrometer:
    :return:
    """
    options = [SINGLE, GS]
    
    if spectrometer == 'BWTEK':
        options = [SINGLE, MS, GS, P3D]
    
    st.sidebar.write('#### Choose type of chart', unsafe_allow_html=True)
    chart_type = st.sidebar.radio(
        '',
        (options), 0)

    st.header(chart_type)
    return chart_type


def convertion_opt():
    st.sidebar.write('#### How would you like to convert the data?', unsafe_allow_html=True)
    spectra_conversion_type = st.sidebar.radio(
        "",
        (RAW, OPT, NORM), key=f'raw')
    
    return spectra_conversion_type
