import streamlit as st

from . import visualisation_options as vo

SINGLE = 'Single spectra'
MS = "Mean spectrum"
GS = "Grouped spectra"
P3D = "Plot 3D"
RAW = "Raw Data"
OPT = "Optimised Data"
NORM = "Normalized"


def show_plot(df, plots_color, template, display_opt):
    """
    Based on uploaded files and denominator it shows either single plot of each spectra (file),
    all spectra on one plot or spectra of mean values
    :param df: DataFrame
    :param display_opt: String
    """
    
    spectra_conversion_type = st.sidebar.radio(
        "How would you like to convert the data?:",
        (RAW, OPT, NORM), key=f'raw'
    )
    
    params = plots_color, template, display_opt, spectra_conversion_type
    
    data_vis_option = {SINGLE: vo.show_single_plots,
                       MS: vo.show_mean_plot,
                       GS: vo.show_grouped_plot,
                       P3D: vo.show_3d_plots}
    
    data_vis_option[display_opt](df, params)


def bwtek_vis_options(df, plots_color, template):
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
    show_plot(df, plots_color, template, display_opt=chart_type)


def vis_options():
    chart_type = st.sidebar.radio(
        'Choose type of chart',
        (SINGLE, GS), 0)
    st.header(chart_type)
    return chart_type
