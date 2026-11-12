import streamlit as st

from constants import LABELS


def get_deg_win(chart_type, spectra_conversion_type, df_columns):
    """
    Fills in right side of webside with sliders for polynomial degree and smoothening window

    Args:
        chart_type (str): type of plot
        spectra_conversion_type (str): type of data preprocessing
        df_columns (list): df column names

    Returns:
        dict: polynomial degree and smoothening window tuple for each data series
    """
    if spectra_conversion_type == 'RAW':
        vals = None

    elif chart_type == 'MS':
        deg = choosing_regression_degree()
        window = choosing_smoothening_window()
        vals = {col: (deg, window) for col in df_columns}

    elif chart_type == 'SINGLE':
        vals = {}
        for col in df_columns:
            # st.write(col)
            vals[col] = (choosing_regression_degree(col), choosing_smoothening_window(col))

    elif chart_type in {'GS', 'P3D'}:
        # with st.beta_expander("Customize spectra", expanded=True):
        adjust_plots_globally = st.radio(
            "Adjust all spectra or each spectrum?",
            ('all', 'each'), index=0)
    
        if adjust_plots_globally == 'all':
            deg = choosing_regression_degree()
            window = choosing_smoothening_window()
            vals = {col: (deg, window) for col in df_columns}
        else:
            vals = {}
            for col in df_columns:
                st.markdown("""
                <hr style="height:1px;border:none;color:#fff;background-color:#999;margin-top:10px;margin-bottom:10px" />
                """,
                            unsafe_allow_html=True)
                st.write(col)
                vals[col] = (choosing_regression_degree(col),
                             choosing_smoothening_window(col))
    else:
        raise ValueError('Unknown chart type')
    
    return vals


def separate_spectra(normalized):
    """
    Shift spectra between each other.
    Depending on the conversion type it takes different values
    :param normalized:
    :return: Int or Float
    """
    # depending on conversion type we have to adjust the scale
    if normalized:
        shift = st.slider(LABELS['SHIFT'], 0.0, 1.0, 0.0, 0.1)
        shift = float(shift)
    else:
        shift = st.slider(LABELS['SHIFT'], 0, 30000, 0, 250)
        shift = int(shift)
    return shift


def choosing_regression_degree(col='default'):
    """
    Slider, choose your polynomial regression degree
    :param col: Str, spectrum name (makes the widget key unique)
    :return: Int, degree for polynomial regression
    """
    return int(st.slider('Polynomial degree', min_value=1, max_value=20, value=5, key=f'{col}_deg'))


def choosing_smoothening_window(col='default'):
    """
    Slider, choose window for rolling function for smoothing the spectra
    :param col: Str, spectrum name (makes the widget key unique)
    :return: Int, window for smoothening
    """
    return int(st.slider('Smoothing window', min_value=1, max_value=20, value=3, key=f'{col}_window'))
