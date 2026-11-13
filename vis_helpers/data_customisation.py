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


BASELINE_LABELS = {'modpoly': 'Polynomial (ModPoly)', 'arpls': 'arPLS (strong fluorescence background)',
                   'snip': 'SNIP (peak clipping)'}
SMOOTHING_LABELS = {'moving_average': 'Moving average', 'savgol': 'Savitzky-Golay (keeps peak heights)'}
ARPLS_LAMBDAS = [10 ** n for n in range(2, 10)]


def processing_settings(columns, allow_each=True):
    """
    Spike removal, baseline and smoothing settings (put inside an expander)
    :param columns: spectra names
    :param allow_each: Bool, allow a polynomial degree for every spectrum separately
    :return: Dict: despike (threshold or None), baseline ((method, param) or None), smoothing ((method, window) or None)
    """
    from vis_helpers.i18n import choice

    settings = {'despike': None, 'baseline': None, 'smoothing': None}

    if st.checkbox(t('Remove spikes (cosmic rays)'), key='despike'):
        settings['despike'] = st.slider(t('Spike threshold'), 3, 30, 10, key='spike_threshold',
                                        help=t('In units of noise. Lower = more points treated as spikes.'))

    if st.checkbox(t('Baseline correction'), key='processed'):
        method = choice('selectbox', t('Baseline method'), list(BASELINE_LABELS), key='baseline_method',
                        format_func=lambda m: t(BASELINE_LABELS[m]))
        if method == 'modpoly':
            if not allow_each or len(columns) == 1 or st.checkbox(t('Same settings for all spectra'), value=True,
                                                                   key='same_settings'):
                param = choosing_regression_degree()
            else:
                param = {}
                for col in columns:
                    st.markdown(f'**{col}**')
                    param[col] = choosing_regression_degree(col)
        elif method == 'arpls':
            param = st.select_slider(t('Smoothness of the baseline (λ)'), ARPLS_LAMBDAS, value=10 ** 6,
                                     key='arpls_lambda', format_func=lambda v: f'10^{len(str(v)) - 1}',
                                     help=t('Higher = stiffer, flatter baseline.'))
        else:
            param = st.slider(t('Half window [cm⁻¹]'), 10, 300, 60, key='snip_window',
                              help=t('Should be larger than the widest peak.'))
        settings['baseline'] = (method, param)

    if st.checkbox(t('Smoothing'), key='smoothing'):
        method = choice('selectbox', t('Smoothing method'), list(SMOOTHING_LABELS), key='smoothing_method',
                        format_func=lambda m: t(SMOOTHING_LABELS[m]))
        window = st.slider(t('Smoothing window'), 3, 51, 7, key='smoothing_window',
                           help=t('Number of points. Savitzky-Golay uses an odd number.'))
        settings['smoothing'] = (method, window)

    return settings
