import streamlit as st

from constants import LABELS


def vis_options():
    """
    Different types of visualisation for other data types
    :return:
    """
    
    options = ["SINGLE", "MS", "GS", "P3D"]
    
    chart_type = st.sidebar.selectbox('Choose type of chart', options, 0,
                                      format_func=lambda x: LABELS[x])
    
    return chart_type


def convertion_opt():
    options = ["RAW", "OPT"]
    
    spectra_conversion_type = st.sidebar.radio(
        "Data representation",
        options,
        key=f'raw',
        format_func=lambda x: LABELS[x])
    
    return spectra_conversion_type
