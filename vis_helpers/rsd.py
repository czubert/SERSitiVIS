import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import analysis, processing
from vis_helpers import background, data_customisation, vis_utils, workspace
from vis_helpers.i18n import t, choice

RSD_TYPES = {'OneP': 'Intensity of one peak', 'P2P': 'Ratio of two peaks'}
PEAK_COLORS = {'Peak 1': 'gold', 'Peak 2': 'green'}
CHART_KEY = 'rsd_chart'


def main(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    st.header(t('Relative Standard Deviation (RSD)'))

    if df is None:
        st.warning(t('Upload spectra in the sidebar (or choose example data)'))
        return

    all_df, df = df, background.samples(df)
    spectra = st.multiselect(t('Spectra'), list(df.columns), default=list(df.columns), key='rsd_spectra')
    if len(spectra) < 2:
        st.warning(t('Choose at least two spectra'))
        background.panel_if_hidden(all_df, df)
        return
    df = df[spectra]

    chart_col, settings_col = st.columns((3, 1))

    with settings_col:
        df, subtraction = background.subtract(df, background.panel(all_df))
        low, high = vis_utils.spectrum_limits(df)
        rsd_type = choice('radio', t('RSD type'), list(RSD_TYPES), key='rsd_type',
                          format_func=lambda r: t(RSD_TYPES[r]))
        peak_names = ['Peak 1', 'Peak 2'] if rsd_type == 'P2P' else ['Peak 1']

        labels = {'Peak 1': t('Peak 1 range'), 'Peak 2': t('Peak 2 range')}
        ranges = {name: vis_utils.range_slider(labels[name], low, high, key=f'rsd_{name}_range')
                  for name in peak_names}
        target = choice('radio', t('Selection on the chart sets'), peak_names, key='rsd_selection_target',
                        format_func=t, horizontal=True) if rsd_type == 'P2P' else 'Peak 1'

        normalized = st.checkbox(t('Normalize chart'), key='rsd_normalize',
                                 help=t('Changes only the chart - RSD is always calculated from the original '
                                        'intensities'))

        round_num = st.slider(t('Decimal places'), 0, 4, 2, 1, key='rsd_decimals')
        with st.expander(t('Chart appearance'), icon=':material/palette:'):
            settings = vis_utils.chart_settings('rsd')

    with chart_col:
        mode, half_window = data_customisation.peak_baseline_switch('rsd')
    peak1, peak2 = ranges['Peak 1'], ranges.get('Peak 2')
    measurable = all(len(processing.trim(df, *peak_range)) >= 2 for peak_range in ranges.values())
    if measurable:
        heights = {'RAW data': analysis.peak_heights(df, peak1, peak2, 'none')}
        if mode != 'none':
            heights['Baseline corrected'] = analysis.peak_heights(df, peak1, peak2, mode, half_window)
        table = analysis.rsd_table(heights)
    baseline_text = data_customisation.describe_peak_baseline(mode, half_window)

    # Normalisation only changes the chart. RSD measures differences in intensity between spectra,
    # normalising each spectrum to its maximum would remove them (RSD of the strongest peak = 0 %).
    plot_df = processing.normalize(df) if normalized else df
    fig = px.line(plot_df, color_discrete_sequence=settings['palette'])
    fig.update_layout(dragmode='select', selectdirection='h')
    colors = {trace.name: trace.line.color for trace in fig.data}
    for name, peak_range in ranges.items():
        if tuple(peak_range) == (low, high):
            continue
        vis_utils.highlight_range(fig, *peak_range, color=PEAK_COLORS[name], opacity=0.15,
                                  annotation_text=t(name), annotation_position='top left')
        if mode != 'none':  # what is subtracted - dotted under every peak
            _, peak_baselines = analysis.peak_window(plot_df, *peak_range, mode, half_window)
            for spectrum in peak_baselines.columns:
                fig.add_trace(go.Scatter(x=peak_baselines.index, y=peak_baselines[spectrum], mode='lines',
                                         line=dict(dash='dot', width=2, color=colors.get(spectrum)),
                                         showlegend=False, hoverinfo='skip'))
    if measurable:  # RSD of the chosen baseline
        rsd = table.loc['RSD[%]'].iloc[-1]
        interval = vis_utils.rsd_interval(rsd / 100, df.shape[1])
        vis_utils.chart_note(fig, f'<b>RSD = {rsd:.{round_num}f} %</b><br>{interval}<br>{baseline_text}')

    with chart_col:
        st.caption(t('Tip: drag on the chart to select the peak range.'))
        vis_utils.show_chart(fig, settings, key=CHART_KEY, selection_mode='box',
                             on_select=lambda: vis_utils.range_from_selection(CHART_KEY, f'rsd_{target}_range',
                                                                              low, high))
        if not measurable:
            st.warning(t('Peak range is too narrow'))
            return

    table.index = [t(i) for i in table.index]
    table.columns = [t(c) for c in table.columns]
    with chart_col:
        st.subheader(t('Results'))
        # upper end of the RSD interval is infinite for 2-3 spectra
        st.table(table.replace(np.inf, np.nan).style.format(f'{{:.{round_num}f}}', na_rep='∞'))
        st.caption(t('95 % CI: the range in which the true RSD of the substrate lies. It narrows with more spectra '
                     '- a measured RSD of 10 % means 6–29 % from 5 spectra and 8–15 % from 20.'))
        vis_utils.download_csv(table, 'rsd.csv', t('Download results (CSV)'), 'rsd_csv')
        vis_utils.report_button('rsd', lambda: build_report(df, ranges, rsd_type, baseline_text, table, subtraction),
                                (rsd_type, ranges, baseline_text, tuple(df.columns), float(df.to_numpy().sum()),
                                 background.describe(subtraction)))


def build_report(df, ranges, rsd_type, baseline_text, table, subtraction=None):
    from core import report

    rep = report.Report(t('Relative Standard Deviation (RSD)'))
    rep.heading(t('Data'))
    rep.key_values({t('Files'): ', '.join(workspace.file_names()) or '—', t('Spectra'): df.shape[1],
                    t('Subtract substrate background'): background.describe(subtraction),
                    t('RSD type'): t(RSD_TYPES[rsd_type]),
                    **{t(f'{name} range'): f'{low} – {high} cm⁻¹' for name, (low, high) in ranges.items()},
                    t('Baseline under the peak'): baseline_text})
    colors = {'Peak 1': report.GOLD, 'Peak 2': '#9BC59D'}
    rep.figure(report.spectra_figure(df, ranges=[(low, high, colors[name]) for name, (low, high) in ranges.items()]))
    rep.heading(t('Results'))
    rep.table(table)
    return rep.to_bytes()
