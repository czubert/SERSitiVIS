import streamlit as st

from constants import LABELS


def vis_options(spectrometer):
    """
    Different types of visualisation for other data types
    :param spectrometer:
    :return:
    """
    options = [LABELS["SINGLE"], LABELS["GS"]]
    
    if spectrometer == 'BWTEK':
        options = [LABELS["SINGLE"], LABELS["GS"], LABELS["MS"], LABELS["P3D"]]
    
    st.sidebar.write('#### Choose type of chart', unsafe_allow_html=True)
    chart_type = st.sidebar.radio(
        '',
        (options), 1)

    st.header(chart_type)
    return chart_type


def convertion_opt():
    st.sidebar.write('#### How would you like to convert the data?', unsafe_allow_html=True)
    spectra_conversion_type = st.sidebar.radio(
        "",
        (LABELS["RAW"], LABELS["OPT"], LABELS["NORM"]), key=f'raw')
    
    return spectra_conversion_type
