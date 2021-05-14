import streamlit as st

from constants import LABELS


def vis_options(spectrometer):
    """
    Different types of visualisation for other data types
    :param spectrometer:
    :return:
    """
    # if spectrometer == 'BWTEK':
    options = [LABELS["SINGLE"], LABELS["MS"], LABELS["GS"], LABELS["P3D"]]
    # else:
    #     options = [LABELS["SINGLE"], LABELS["GS"]]

    st.sidebar.write('#### Choose type of chart', unsafe_allow_html=True)
    chart_type = st.sidebar.selectbox('', options, 2)

    return chart_type


def convertion_opt():
    st.sidebar.write('#### How would you like to convert the data?', unsafe_allow_html=True)
    spectra_conversion_type = st.sidebar.selectbox(
        "",
        (LABELS["RAW"], LABELS["OPT"], LABELS["NORM"]), key=f'raw')
    
    return spectra_conversion_type
