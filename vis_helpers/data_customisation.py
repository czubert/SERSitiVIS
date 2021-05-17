import streamlit as st

from constants import LABELS
from processing import utils
from vis_helpers import vis_utils


def get_deg_win(df, chart_type, spectra_conversion_type, cols_right, df_columns):
    """
    Fills in right side of webside with sliders for polynomial degree and smoothening window

    Args:
        chart_type (str): type of plot
        spectra_conversion_type (str): type of data preprocessing
        cols_right (list): list of right side st.beta_columns
        df_columns (list): df column names

    Returns:
        dict: polynomial degree and smoothening window tuple for each data series
    """
    if spectra_conversion_type == LABELS['RAW']:
        vals = None
    
    elif chart_type == LABELS['MS']:
        with cols_right[0]:
            deg = utils.choosing_regression_degree()
            window = utils.choosing_smoothening_window()
            vals = {col: (deg, window) for col in df_columns}
    
    elif chart_type == LABELS['SINGLE']:
        vals = {}
        
        for col_right, col in zip(cols_right, df_columns):
            with col_right:
                st.write(col)
                vals[col] = (utils.choosing_regression_degree(None, col), utils.choosing_smoothening_window(None, col))
    
    elif chart_type in {LABELS['GS'], LABELS['P3D']}:
        
        with cols_right[0]:
            with st.beta_expander("Customize spectra", expanded=True):
                adjust_plots_globally = st.radio(
                    "Adjust all spectra or each spectrum?",
                    ('all', 'each'), index=0)

                df = vis_utils.trim_spectra(df)
    
                if adjust_plots_globally == 'all':
                    deg = utils.choosing_regression_degree()
                    window = utils.choosing_smoothening_window()
                    vals = {col: (deg, window) for col in df_columns}
                else:
                    vals = {}
                    for col in df_columns:
                        st.write(col)
                        vals[col] = (utils.choosing_regression_degree(None, col),
                                     utils.choosing_smoothening_window(None, col))
    else:
        raise ValueError('Unknown chart type')
    
    return df, vals


def separate_spectra(spectra_conversion_type):
    """
    Shift spectra between each other.
    Depending on the conversion type it takes different values
    :param spectra_conversion_type: Str, Optimisation/Normalization
    :return: Int or Float
    """
    # depending on conversion type we have to adjust the scale
    if spectra_conversion_type == LABELS['NORM']:
        shift = st.slider(LABELS['SHIFT'], 0.0, 1.0, 0.0, 0.1)
    else:
        shift = st.slider(LABELS['SHIFT'], 0, 30000, 0, 250)
    return shift
