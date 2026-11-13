import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import analysis, processing
from vis_helpers import vis_utils, workspace
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

    spectra = st.multiselect(t('Spectra'), list(df.columns), default=list(df.columns), key='rsd_spectra')
    if len(spectra) < 2:
        st.warning(t('Choose at least two spectra'))
        return
    df = df[spectra]
    low, high = vis_utils.spectrum_limits(df)

    chart_col, settings_col = st.columns((3, 1))

    with settings_col:
        rsd_type = choice('radio', t('RSD type'), list(RSD_TYPES), key='rsd_type',
                          format_func=lambda r: t(RSD_TYPES[r]))
        peak_names = ['Peak 1', 'Peak 2'] if rsd_type == 'P2P' else ['Peak 1']

        labels = {'Peak 1': t('Peak 1 range'), 'Peak 2': t('Peak 2 range')}
        ranges = {name: vis_utils.range_slider(labels[name], low, high, key=f'rsd_{name}_range')
                  for name in peak_names}
        target = choice('radio', t('Selection on the chart sets'), peak_names, key='rsd_selection_target',
                        format_func=t, horizontal=True) if rsd_type == 'P2P' else 'Peak 1'

        degree = st.slider(t('Polynomial degree for baseline correction'), 0, 20, 1, 1, key='rsd_degree',
                           help=t('Baseline is fitted within each peak range - shown as dotted lines on the chart'))
        normalized = st.checkbox(t('Normalize chart'), key='rsd_normalize',
                                 help=t('Changes only the chart - RSD is always calculated from the original '
                                        'intensities'))

        round_num = st.slider(t('Decimal places'), 0, 4, 2, 1, key='rsd_decimals')
        with st.expander(t('Chart appearance'), icon=':material/palette:'):
            settings = vis_utils.chart_settings('rsd')

    # Normalisation only changes the chart. RSD measures differences in intensity between spectra,
    # normalising each spectrum to its maximum would remove them (RSD of the strongest peak = 0 %).
    plot_df = processing.normalize(df) if normalized else df

    fig = px.line(plot_df, color_discrete_sequence=settings['palette'])
    fig.update_layout(dragmode='select', selectdirection='h')
    colors = {trace.name: trace.line.color for trace in fig.data}

    for name, peak_range in ranges.items():
        if tuple(peak_range) == (low, high):
            continue
        fig.add_vrect(x0=peak_range[0], x1=peak_range[1], line_width=0, fillcolor=PEAK_COLORS[name], opacity=0.15,
                      annotation_text=t(name), annotation_position='top left')
        # baselines subtracted within the peak range, so the effect of the polynomial degree is visible
        peak = processing.trim(plot_df, *peak_range)
        if len(peak) > 1:
            for spectrum in peak.columns:
                fig.add_trace(go.Scatter(x=peak.index, y=processing.baseline(peak[spectrum], degree, x=peak.index),
                                         mode='lines', line=dict(dash='dot', width=2, color=colors.get(spectrum)),
                                         showlegend=False, hoverinfo='skip'))

    with chart_col:
        st.caption(t('Tip: drag on the chart to select the peak range.'))
        vis_utils.show_chart(fig, settings, key=CHART_KEY, selection_mode='box',
                             on_select=lambda: vis_utils.range_from_selection(CHART_KEY, f'rsd_{target}_range',
                                                                              low, high))

    peaks = {name: processing.trim(df, *peak_range) for name, peak_range in ranges.items()}
    if any(len(peak) < 2 for peak in peaks.values()):
        st.warning(t('Peak range is too narrow'))
        return

    table = analysis.rsd_table(peaks['Peak 1'], peaks.get('Peak 2'), degree)
    table.index = [t(i) for i in table.index]
    table.columns = [t(c) for c in table.columns]

    with chart_col:
        st.subheader(t('Results'))
        st.table(table.style.format(f'{{:.{round_num}f}}'))
        vis_utils.download_csv(table, 'rsd.csv', t('Download results (CSV)'), 'rsd_csv')
        vis_utils.report_button('rsd', lambda: build_report(df, ranges, rsd_type, degree, table),
                                (rsd_type, ranges, degree, tuple(df.columns), float(df.to_numpy().sum())))


def build_report(df, ranges, rsd_type, degree, table):
    from core import report

    rep = report.Report(t('Relative Standard Deviation (RSD)'))
    rep.heading(t('Data'))
    rep.key_values({t('Files'): ', '.join(workspace.file_names()) or '—', t('Spectra'): df.shape[1],
                    t('RSD type'): t(RSD_TYPES[rsd_type]),
                    **{t(f'{name} range'): f'{low} – {high} cm⁻¹' for name, (low, high) in ranges.items()},
                    t('Polynomial degree for baseline correction'): degree})
    colors = {'Peak 1': report.GOLD, 'Peak 2': '#9BC59D'}
    rep.figure(report.spectra_figure(df, ranges=[(low, high, colors[name]) for name, (low, high) in ranges.items()]))
    rep.heading(t('Results'))
    rep.table(table)
    return rep.to_bytes()
