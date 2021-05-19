import streamlit as st

from constants import LABELS


def vis_options():
    """
    Different types of visualisation for other data types
    :return:
    """
    options = [LABELS["SINGLE"], LABELS["MS"], LABELS["GS"], LABELS["P3D"]]
    
    st.sidebar.write('#### Choose type of chart', unsafe_allow_html=True)
    chart_type = st.sidebar.selectbox('', options, 2)
    
    return chart_type


def convertion_opt():
    st.sidebar.write('#### Data representation', unsafe_allow_html=True)
    spectra_conversion_type = st.sidebar.radio(
        "",
        (LABELS["RAW"], LABELS["OPT"]), key=f'raw')
    
    return spectra_conversion_type
