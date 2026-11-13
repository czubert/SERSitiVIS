import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import calibration, processing
from vis_helpers import vis_utils
from vis_helpers.i18n import t, choice

CHART_KEY = 'cal_chart'
RANGE_KEY = 'cal_range'


def fmt(value, unit=''):
    if value is None or not np.isfinite(value):
        return '—'
    return f'{value:.3g} {unit}'.strip()


def main(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    st.header(t('Calibration curve and limit of detection (LOD)'))

    if df is None:
        st.warning(t('Upload spectra in the sidebar (or choose example data)'))
        st.info(t('Upload spectra measured at several concentrations (replicates welcome). Concentrations are read '
                  'from file names, e.g. "R6G_5x10-6M_1.txt" or "sample_1ppm.csv" - you can correct them.'))
        return

    low, high = vis_utils.spectrum_limits(df)
    chart_col, settings_col = st.columns((3, 1))

    # # Settings
    with settings_col:
        peak_range = vis_utils.range_slider(t('Peak range'), low, high, key=RANGE_KEY)
        method = choice('radio', t('Signal'), ['height', 'area'], key='cal_method', horizontal=True,
                        format_func=lambda m: t('Peak height') if m == 'height' else t('Peak area'))
        degree = st.slider(t('Polynomial degree for baseline correction'), 0, 5, 1, key='cal_degree',
                           help=t('Baseline is fitted within the peak range - shown as dotted lines on the chart'))
        log_x = choice('radio', t('Concentration axis'), ['linear', 'log'], key='cal_scale', horizontal=True,
                       format_func=lambda s: t('Linear') if s == 'linear' else t('Logarithmic')) == 'log'

    # # Concentrations (parsed from names, editable)
    parsed, parsed_unit = calibration.concentrations_from_names(df.columns)
    with settings_col:
        unit = st.selectbox(t('Unit'), calibration.UNITS,
                            index=calibration.UNITS.index(parsed_unit) if parsed_unit else 0, key='cal_unit')
    with st.expander(t('Concentrations'), expanded=parsed.isna().any(), icon=':material/edit:'):
        st.caption(t('Read from file names - correct them if needed. Use 0 for blank samples.'))
        table = pd.DataFrame({t('Spectrum'): parsed.index, t('Concentration'): parsed.to_numpy()})
        edited = st.data_editor(table, key='cal_concentrations', hide_index=True, width='stretch',
                                disabled=[t('Spectrum')],
                                column_config={t('Concentration'): st.column_config.NumberColumn(
                                    f'{t("Concentration")} [{unit}]', min_value=0.0, format='%g')})
    concentration = pd.Series(edited[t('Concentration')].to_numpy(dtype=float), index=df.columns)

    # # Spectra with the peak range and fitted baselines
    fig = px.line(df, color_discrete_sequence=vis_utils.SERSITIVE_PALETTE)
    fig.update_layout(dragmode='select', selectdirection='h', height=420)
    if tuple(peak_range) != (low, high):
        fig.add_vrect(x0=peak_range[0], x1=peak_range[1], line_width=0, fillcolor='gold', opacity=0.2)
        window = processing.trim(df, *peak_range)
        if len(window) > 2:
            colors = {trace.name: trace.line.color for trace in fig.data}
            for spectrum in window.columns:
                fig.add_trace(go.Scatter(x=window.index, y=processing.baseline(window[spectrum], degree,
                                                                              x=window.index),
                                         mode='lines', line=dict(dash='dot', width=2, color=colors.get(spectrum)),
                                         showlegend=False, hoverinfo='skip'))

    with chart_col:
        st.caption(t('Tip: drag on the chart to select the peak range.'))
        settings = vis_utils.default_chart_settings()
        vis_utils.show_chart(fig, settings, key=CHART_KEY, selection_mode='box',
                             on_select=lambda: vis_utils.range_from_selection(CHART_KEY, RANGE_KEY, low, high))

    if tuple(peak_range) == (low, high):
        st.info(t('Select the peak range on the chart (drag) or with the slider.'))
        return

    # # Calibration
    try:
        signal = calibration.peak_signal(df, *peak_range, method=method, degree=degree)
    except ValueError:
        st.warning(t('Peak range is too narrow'))
        return

    known = concentration.notna()
    if known.sum() < 2 or concentration[known].nunique() < 2:
        st.warning(t('Enter concentrations for at least two different levels.'))
        return

    blanks = int((concentration == 0).sum())
    with settings_col:
        sigma_source = choice('radio', t('Standard deviation for LOD'), ['regression', 'blank'], key='cal_sigma',
                              format_func=lambda s: t('Residuals of the fit') if s == 'regression'
                              else t('Blank spectra (concentration 0)'),
                              help=t('Blank: LOD = 3·SD(blank)/slope. Fit: LOD = 3.3·SD(residuals)/slope.'))
    try:
        result = calibration.fit_calibration(concentration[known], signal[known], log_x=log_x,
                                             use_blank=sigma_source == 'blank')
    except ValueError as e:
        st.warning(t(str(e)))
        return

    if result.slope <= 0:
        st.warning(t('The signal does not increase with concentration, so LOD cannot be calculated. '
                     'Check the concentrations and the peak range.'))
    elif np.isfinite(result.r2) and result.r2 < 0.9:
        st.warning(t('Poor linearity (R² < 0.9) - LOD and LOQ are not reliable.'))
    if sigma_source == 'blank' and blanks < 2:
        st.warning(t('At least two blank (concentration 0) spectra are needed'))
    if log_x and sigma_source == 'regression':
        st.info(t('With a logarithmic axis LOD is calculated from blank spectra - choose them as the source of the '
                  'standard deviation.'))

    summary = calibration.summary_by_concentration(concentration[known], signal[known])

    with chart_col:
        st.subheader(t('Calibration curve'))
        c = st.columns(4)
        c[0].metric('LOD', fmt(result.lod, unit), border=True)
        c[1].metric('LOQ', fmt(result.loq, unit), border=True)
        c[2].metric('R²', fmt(result.r2), border=True)
        c[3].metric(t('Slope'), fmt(result.slope), border=True)

        x_label = f'log₁₀(c / {unit})' if log_x else 'c'
        sign = '+' if result.intercept >= 0 else '−'
        st.markdown(f'y = {result.slope:.4g} · {x_label} {sign} {abs(result.intercept):.4g}')

        points = summary.reset_index()
        if log_x:
            points = points[points['c'] > 0]
        cal_fig = go.Figure()
        cal_fig.add_trace(go.Scatter(x=concentration[known], y=signal[known], mode='markers', name=t('Spectra'),
                                     marker=dict(color=vis_utils.SERSITIVE_PALETTE[1], size=7, opacity=0.5)))
        cal_fig.add_trace(go.Scatter(x=points['c'], y=points['mean'], mode='markers', name=t('Mean ± SD'),
                                     error_y=dict(type='data', array=points['std'].fillna(0)),
                                     marker=dict(color=vis_utils.SERSITIVE_PALETTE[0], size=11)))
        fit_x = np.logspace(np.log10(points['c'].min()), np.log10(points['c'].max()), 100) if log_x \
            else np.linspace(0, points['c'].max(), 100)
        cal_fig.add_trace(go.Scatter(x=fit_x, y=result.predict(fit_x), mode='lines', name=t('Fit'),
                                     line=dict(color=vis_utils.SERSITIVE_PALETTE[2], width=3)))
        if log_x:
            cal_fig.update_xaxes(type='log')
        cal_settings = vis_utils.default_chart_settings()
        cal_settings['titles'] = {'x': f'{t("Concentration")} [{unit}]',
                                  'y': t('Peak height') if method == 'height' else t('Peak area'), 'title': ''}
        cal_fig.update_layout(hovermode='closest', height=450)
        vis_utils.show_chart(cal_fig, cal_settings, lines=False)

        table = summary.rename(columns={'mean': t('Mean'), 'std': 'SD', 'count': 'n', 'rsd': 'RSD [%]'})
        table.index.name = f'{t("Concentration")} [{unit}]'
        st.dataframe(table.style.format({t('Mean'): '{:.4g}', 'SD': '{:.3g}', 'RSD [%]': '{:.1f}'}))

        export = pd.DataFrame({t('Spectrum'): df.columns, f'{t("Concentration")} [{unit}]': concentration.to_numpy(),
                               t('Signal'): signal.reindex(df.columns).to_numpy()})
        results = pd.DataFrame({t('Spectrum'): ['slope', 'intercept', 'R2', 'LOD', 'LOQ', 'SD used for LOD'],
                                t('Signal'): [result.slope, result.intercept, result.r2, result.lod, result.loq,
                                              result.sigma]})
        vis_utils.download_csv(pd.concat([export, results]), 'calibration.csv', t('Download results (CSV)'),
                               'cal_csv', index=False)
