import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import calibration, processing
from vis_helpers import vis_utils, workspace
from vis_helpers.i18n import t, choice

CHART_KEY = 'cal_chart'
RANGE_KEY = 'cal_range'
DATA_KEY = '_cal_data'  # which data the stored peak range belongs to
CONC_KEY = '_cal_concentrations'
UNIT_KEY = 'cal_unit'
PREVIOUS_UNIT_KEY = '_cal_previous_unit'
EDITOR_KEY = 'cal_concentrations'


def fmt(value, unit=''):
    if value is None or not np.isfinite(value):
        return '—'
    return f'{value:.3g} {unit}'.strip()


def rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    return f'rgba({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}, {alpha})'


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
    # new data -> start again from the strongest peak
    data_id = (tuple(df.columns), low, high)
    if st.session_state.get(DATA_KEY) != data_id:
        st.session_state[DATA_KEY] = data_id
        for key in (RANGE_KEY, CONC_KEY, UNIT_KEY, PREVIOUS_UNIT_KEY):
            st.session_state.pop(key, None)

    # # Step 1 - peak
    st.subheader(f'1. {t("Peak")}')
    chart_col, settings_col = st.columns((3, 1))
    with settings_col:
        peak_range = vis_utils.range_slider(t('Peak range'), low, high, key=RANGE_KEY,
                                            default=calibration.strongest_peak_range(df))
        method = choice('radio', t('Signal'), ['height', 'area'], key='cal_method', horizontal=True,
                        format_func=lambda m: t('Peak height') if m == 'height' else t('Peak area'))
        degree = st.slider(t('Polynomial degree for baseline correction'), 0, 5, 1, key='cal_degree',
                           help=t('Baseline is fitted within the peak range - shown as dotted lines on the chart'))

    palette = vis_utils.SERSITIVE_PALETTE
    colors = {col: palette[i % len(palette)] for i, col in enumerate(df.columns)}

    with chart_col:
        st.caption(t('Tip: drag on the chart to select the peak range.'))
        fig = px.line(df, color_discrete_map=colors)
        fig.update_layout(dragmode='select', selectdirection='h', height=330, showlegend=False)
        fig.add_vrect(x0=peak_range[0], x1=peak_range[1], line_width=0, fillcolor='gold', opacity=0.25)
        vis_utils.show_chart(fig, vis_utils.default_chart_settings(), key=CHART_KEY, selection_mode='box',
                             on_select=lambda: vis_utils.range_from_selection(CHART_KEY, RANGE_KEY, low, high))

    window = processing.trim(df, *peak_range)
    if len(window) < 3:
        st.warning(t('Peak range is too narrow'))
        return
    signal = calibration.peak_signal(df, *peak_range, method=method, degree=degree)

    # zoom on the peak: what exactly is measured (baseline + height or area)
    zoom = go.Figure()
    for spectrum in window.columns:
        color = colors[spectrum]
        base = processing.baseline(window[spectrum], degree, x=window.index)
        zoom.add_trace(go.Scatter(x=window.index, y=base, mode='lines', line=dict(dash='dot', width=1.5, color=color),
                                  showlegend=False, hoverinfo='skip'))
        if method == 'area':
            zoom.add_trace(go.Scatter(x=window.index, y=window[spectrum], mode='lines', name=spectrum,
                                      line=dict(color=color), fill='tonexty', fillcolor=rgba(color, 0.15)))
        else:
            zoom.add_trace(go.Scatter(x=window.index, y=window[spectrum], mode='lines', name=spectrum,
                                      line=dict(color=color)))
            top = (window[spectrum] - base).idxmax()
            zoom.add_trace(go.Scatter(x=[top, top], y=[base[window.index.get_loc(top)], window[spectrum][top]],
                                      mode='lines+markers', line=dict(color=color, width=3),
                                      marker=dict(size=6), showlegend=False, hoverinfo='skip'))
    with chart_col:
        zoom_settings = vis_utils.default_chart_settings()
        zoom_settings['titles']['title'] = t('Peak - measured signal')
        zoom.update_layout(height=330, showlegend=False)
        vis_utils.show_chart(zoom, zoom_settings, lines=False)

    # # Step 2 - concentrations
    st.subheader(f'2. {t("Concentrations")}')
    parsed, parsed_unit = calibration.concentrations_from_names(df.columns)
    table_col, info_col = st.columns((3, 1))
    with info_col:
        units = [u for u in calibration.UNITS if u != 'uM']
        st.session_state.setdefault(UNIT_KEY, parsed_unit if parsed_unit in units else units[0])
        unit = st.selectbox(t('Unit'), units, key=UNIT_KEY,
                            help=t('Changing the unit converts the values (e.g. 1 µM = 0.001 mM).'))
        st.caption(t('Read from file names: {found} of {total}. Correct them if needed, use 0 for blank samples.')
                   .format(found=int(parsed.notna().sum()), total=len(parsed)))
    # concentrations kept in session_state - the table widget would forget edits when its input data changes
    store = st.session_state.setdefault(CONC_KEY, {})  # values typed in by the user, in the current unit
    previous_unit = st.session_state.get(PREVIOUS_UNIT_KEY, unit)
    if previous_unit != unit:  # convert typed values to the new unit
        for name, value in store.items():
            converted = calibration.convert(value, previous_unit, unit)
            store[name] = value if converted is None else converted
    st.session_state[PREVIOUS_UNIT_KEY] = unit

    def from_names(name):
        if not parsed_unit or np.isnan(parsed[name]):
            return parsed[name]
        converted = calibration.convert(parsed[name], parsed_unit, unit)
        return parsed[name] if converted is None else float(f'{converted:.10g}')

    concentration = pd.Series({name: store.get(name, from_names(name)) for name in df.columns}, dtype=float)

    def on_edit():
        for row, change in st.session_state[EDITOR_KEY].get('edited_rows', {}).items():
            if t('Concentration') in change:
                value = change[t('Concentration')]
                store[df.columns[int(row)]] = np.nan if value is None else float(value)

    with table_col:
        table = pd.DataFrame({t('Spectrum'): concentration.index, t('Concentration'): concentration.to_numpy()})
        st.data_editor(table, key=EDITOR_KEY, hide_index=True, width='stretch', disabled=[t('Spectrum')],
                       on_change=on_edit,
                       column_config={t('Concentration'): st.column_config.NumberColumn(
                           f'{t("Concentration")} [{unit}]', min_value=0.0, format='%.6g')})

    # # Step 3 - calibration curve
    st.subheader(f'3. {t("Calibration curve")}')
    known = concentration.notna()
    if known.sum() < 2 or concentration[known].nunique() < 2:
        st.warning(t('Enter concentrations for at least two different levels in the table above (step 2).'))
        return

    result_col, options_col = st.columns((3, 1))
    with options_col:
        log_x = choice('radio', t('Concentration axis'), ['linear', 'log'], key='cal_scale', horizontal=True,
                       format_func=lambda s: t('Linear') if s == 'linear' else t('Logarithmic')) == 'log'
        sigma_source = choice('radio', t('Standard deviation for LOD'), ['regression', 'blank'], key='cal_sigma',
                              format_func=lambda s: t('Residuals of the fit') if s == 'regression'
                              else t('Blank spectra (concentration 0)'),
                              help=t('Blank: LOD = 3·SD(blank)/slope. Fit: LOD = 3.3·SD(residuals)/slope.'))

    with result_col:
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
        if log_x and sigma_source == 'regression':
            st.info(t('With a logarithmic axis LOD is calculated from blank spectra - choose them as the source of '
                      'the standard deviation.'))

        c = st.columns(4)
        c[0].metric('LOD', fmt(result.lod, unit), border=True)
        c[1].metric('LOQ', fmt(result.loq, unit), border=True)
        c[2].metric('R²', fmt(result.r2), border=True)
        c[3].metric(t('Slope'), fmt(result.slope), border=True)

        x_label = f'log₁₀(c / {unit})' if log_x else 'c'
        sign = '+' if result.intercept >= 0 else '−'
        st.markdown(f'y = {result.slope:.4g} · {x_label} {sign} {abs(result.intercept):.4g}')

        summary = calibration.summary_by_concentration(concentration[known], signal[known])
        points = summary.reset_index()
        if log_x:
            points = points[points['c'] > 0]
        cal_fig = go.Figure()
        cal_fig.add_trace(go.Scatter(x=concentration[known], y=signal[known], mode='markers', name=t('Spectra'),
                                     marker=dict(color=palette[1], size=7, opacity=0.6)))
        cal_fig.add_trace(go.Scatter(x=points['c'], y=points['mean'], mode='markers', name=t('Mean ± SD'),
                                     error_y=dict(type='data', array=points['std'].fillna(0)),
                                     marker=dict(color=palette[0], size=11)))
        fit_x = np.logspace(np.log10(points['c'].min()), np.log10(points['c'].max()), 100) if log_x \
            else np.linspace(0, points['c'].max(), 100)
        cal_fig.add_trace(go.Scatter(x=fit_x, y=result.predict(fit_x), mode='lines', name=t('Fit'),
                                     line=dict(color=palette[2], width=3)))
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
        vis_utils.report_button(
            'calibration',
            lambda: build_report(df, peak_range, method, degree, unit, log_x, sigma_source, result, summary,
                                 concentration[known], signal[known]),
            (peak_range, method, degree, unit, log_x, sigma_source, tuple(concentration.fillna(-1)),
             float(df.to_numpy().sum())))


def build_report(df, peak_range, method, degree, unit, log_x, sigma_source, result, summary, concentration, signal):
    from core import report

    signal_name = t('Peak height') if method == 'height' else t('Peak area')
    rep = report.Report(t('Calibration curve and limit of detection (LOD)'))
    rep.heading(t('Data'))
    rep.key_values({t('Files'): ', '.join(workspace.file_names()) or '—', t('Spectra'): df.shape[1],
                    t('Peak range'): f'{peak_range[0]} – {peak_range[1]} cm⁻¹', t('Signal'): signal_name,
                    t('Polynomial degree for baseline correction'): degree,
                    t('Concentration axis'): t('Logarithmic') if log_x else t('Linear'),
                    t('Standard deviation for LOD'): t('Residuals of the fit') if sigma_source == 'regression'
                    else t('Blank spectra (concentration 0)')})
    rep.heading(t('Results'))
    x_label = f'log10(c / {unit})' if log_x else 'c'
    rep.key_values({'LOD': f'{fmt(result.lod, unit)}', 'LOQ': f'{fmt(result.loq, unit)}', 'R²': fmt(result.r2),
                    t('Slope'): fmt(result.slope),
                    'y =': f'{result.slope:.4g} · {x_label} {"+" if result.intercept >= 0 else "−"} '
                           f'{abs(result.intercept):.4g}'})
    points = summary.reset_index()
    if log_x:
        points = points[points['c'] > 0]
    fit_x = np.logspace(np.log10(points['c'].min()), np.log10(points['c'].max()), 100) if log_x \
        else np.linspace(0, points['c'].max(), 100)
    rep.figure(report.scatter_figure(concentration, signal, f'{t("Concentration")} [{unit}]', signal_name,
                                     line=(fit_x, result.predict(fit_x)),
                                     errors=(points['c'], points['mean'], points['std'].fillna(0)), log_x=log_x),
               width=150)
    table = summary.rename(columns={'mean': t('Mean'), 'std': 'SD', 'count': 'n', 'rsd': 'RSD [%]'})
    table.index.name = f'{t("Concentration")} [{unit}]'
    rep.table(table)
    rep.figure(report.spectra_figure(df, ranges=[(peak_range[0], peak_range[1], report.GOLD)], legend=False))
    rep.text(t('LOD/LOQ from the fit: 3.3·SD(residuals)/slope and 10·SD/slope (ICH Q2). From blank spectra: '
               '3·SD(blank)/slope and 10·SD/slope.'), size=8)
    return rep.to_bytes()
