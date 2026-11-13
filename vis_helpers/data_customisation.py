import streamlit as st

from vis_helpers.i18n import t


def choosing_regression_degree(col='default'):
    """
    :param col: Str, spectrum name (makes the widget key unique)
    :return: Int, polynomial degree for baseline correction
    """
    return int(st.slider(t('Polynomial degree'), min_value=1, max_value=20, value=5, key=f'{col}_deg',
                         help=t('Higher degree follows the background more closely, but may cut into broad peaks.')))


def choosing_smoothening_window(col='default'):
    """
    :param col: Str, spectrum name (makes the widget key unique)
    :return: Int, window (number of points) for smoothing
    """
    return int(st.slider(t('Smoothing window'), min_value=1, max_value=20, value=3, key=f'{col}_window',
                         help=t('Number of points averaged. 1 = no smoothing.')))


def processing_params(columns, allow_each=True):
    """
    Baseline correction / smoothing settings
    :param columns: spectra names
    :param allow_each: Bool, let the user set parameters for every spectrum separately
    :return: Dict {column: (polynomial degree, smoothing window)}
    """
    if not allow_each or len(columns) == 1 or st.checkbox(t('Same settings for all spectra'), value=True,
                                                           key='same_settings'):
        deg, window = choosing_regression_degree(), choosing_smoothening_window()
        return {col: (deg, window) for col in columns}

    params = {}
    for col in columns:
        st.markdown(f'**{col}**')
        params[col] = (choosing_regression_degree(col), choosing_smoothening_window(col))
    return params
