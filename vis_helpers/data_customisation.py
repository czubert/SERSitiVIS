import streamlit as st

from core import processing

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


BASELINE_LABELS = {'snip': 'SNIP (peak clipping)', 'modpoly': 'Polynomial (ModPoly)',  # the first one is the default
                   'arpls': 'arPLS (strong fluorescence background)'}
SMOOTHING_LABELS = {'moving_average': 'Moving average', 'savgol': 'Savitzky-Golay (keeps peak heights)'}
ARPLS_LAMBDAS = [10 ** n for n in range(2, 10)]
SNIP_HALF_WINDOW = processing.SNIP_HALF_WINDOW
PEAK_BASELINES = {'snip': 'SNIP', 'line': 'Straight line under the peak', 'none': 'None (absolute height)'}


def snip_half_window(key, label=None, **kwargs):
    """Slider for the SNIP half window [cm-1] - the same on every page"""
    return st.slider(label or t('Half window [cm⁻¹]'), 10, 300, SNIP_HALF_WINDOW, key=key, **kwargs,
                     help=t('About twice the width (FWHM) of the peaks, e.g. 40 cm⁻¹ for p-MBA. Too small cuts into '
                            'the peaks, too large leaves fluorescence under them.'))


def describe_peak_baseline(mode, half_window):
    """'SNIP, 40 cm⁻¹' / 'Straight line under the peak' / 'None (absolute height)' - for charts and reports"""
    return f'SNIP, {half_window} cm⁻¹' if mode == 'snip' else t(PEAK_BASELINES[mode])


def peak_baseline_switch(key):
    """
    Baseline under the measured peaks, put above the chart: switching it changes the result on the chart at once
    :return: (mode - key of PEAK_BASELINES, SNIP half window)
    """
    from vis_helpers.i18n import choice

    left, right = st.columns((3, 2), vertical_alignment='bottom')
    with left:
        mode = choice('radio', t('Baseline under the peak'), list(PEAK_BASELINES), key=f'{key}_baseline',
                      horizontal=True, format_func=lambda m: t(PEAK_BASELINES[m]),
                      help=t('What counts as zero under the peak. SNIP: baseline of the whole spectrum. Straight '
                             'line: fitted under the peak range only. None: absolute height, fluorescence and '
                             'background included - e.g. a peak 10 000 high on a 30 000 background counts as 40 000.'))
    with right:
        half_window = snip_half_window(f'{key}_half_window', t('SNIP baseline: half window [cm⁻¹]'),
                                       disabled=mode != 'snip')
    return mode, half_window


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
            param = snip_half_window('snip_window')
        settings['baseline'] = (method, param)

    if st.checkbox(t('Smoothing'), key='smoothing'):
        method = choice('selectbox', t('Smoothing method'), list(SMOOTHING_LABELS), key='smoothing_method',
                        format_func=lambda m: t(SMOOTHING_LABELS[m]))
        window = st.slider(t('Smoothing window'), 3, 51, 7, key='smoothing_window',
                           help=t('Number of points. Savitzky-Golay uses an odd number.'))
        settings['smoothing'] = (method, window)

    return settings
