import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import calibration, peaks, processing
from vis_helpers import manual, data_customisation, vis_utils, workspace
from vis_helpers.i18n import t, choice

NORMALIZATIONS = {'none': 'None', 'minmax': 'Min-max (0-1)', 'max': 'Maximum = 1', 'area': 'Area = 1',
                  'vector': 'Vector (Euclidean norm = 1)', 'snv': 'SNV (mean 0, SD 1)',
                  'peak': 'Reference peak = 1 (internal standard)'}
CHART_TYPES = {'GS': 'Grouped spectra', 'SINGLE': 'Single spectrum', 'MS': 'Mean spectrum', 'P3D': '3D plot'}


def visualisation(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    if df is None:
        manual.show_manual()
        return

    st.header(t('Visualisation'))
    chart_col, settings_col = st.columns((3, 1))

    with settings_col:
        # header shows the current choice, so the expander can stay closed
        current = st.session_state.get('_chart_type', 'GS')
        with st.expander(f'{t("Chart type")}: {t(CHART_TYPES.get(current, CHART_TYPES["GS"]))}',
                         icon=':material/insert_chart:'):
            chart_type = choice('radio', t('Chart type'), list(CHART_TYPES), key='chart_type',
                                format_func=lambda c: t(CHART_TYPES[c]), label_visibility='collapsed')
        if chart_type == 'SINGLE':
            df = df[[vis_utils.spectrum_stepper(df.columns, key='single_spectrum')]]
        elif chart_type == 'MS':
            df = df.mean(axis=1).rename(t('Average')).to_frame()

        with st.expander(t('Range'), icon=':material/straighten:'):
            df = vis_utils.trim_spectra(df)
            if chart_type == 'GS':
                shift = st.slider(t('Separate spectra from each other'), 0.0, 1.0, 0.0, 0.05, key='shift')

        with st.expander(t('Processing'), icon=':material/tune:', expanded=True):
            steps_settings = data_customisation.processing_settings(df.columns,
                                                                    allow_each=chart_type in {'GS', 'P3D'})
            spike_note = st.empty()
            processed = steps_settings['baseline'] is not None or steps_settings['smoothing'] is not None
            show_steps = processed and chart_type in {'SINGLE', 'MS'} and st.checkbox(
                t('Show baseline and intermediate steps'), key='show_steps')
            normalization = choice('selectbox', t('Normalization'), ['none'] + processing.NORMALIZATION_METHODS,
                                   key='normalization', format_func=lambda n: t(NORMALIZATIONS[n]))
            if normalization == 'peak':
                reference_limits = vis_utils.spectrum_limits(df)
                reference = vis_utils.range_slider(t('Reference peak range'), *reference_limits,
                                                   key='reference_peak',
                                                   default=calibration.strongest_peak_range(df))
                if chart_type != 'P3D':
                    st.caption(t('Tip: drag on the chart to select the peak range.'))

        if chart_type != 'P3D':
            with st.expander(t('Peaks'), icon=':material/location_on:', expanded=st.session_state.get('peaks', False)):
                show_peaks = st.checkbox(t('Find and label peaks'), key='peaks')
                if show_peaks:
                    peak_options = dict(
                        prominence=st.slider(t('Sensitivity - minimal peak prominence [%]'), 1, 50, 5, key='peak_prom',
                                             help=t('How much a peak must rise above its surroundings, in % of the '
                                                    'spectrum intensity range. Lower = more peaks.')) / 100,
                        min_distance=st.slider(t('Minimal distance between peaks [cm⁻¹]'), 1, 100, 10,
                                               key='peak_distance'),
                        max_peaks=st.slider(t('Maximal number of labels per spectrum'), 1, 50, 10, key='peak_max'))
        else:
            show_peaks = False

        with st.expander(t('Chart appearance'), icon=':material/palette:'):
            settings = vis_utils.chart_settings('vis')

    # processing: spikes -> baseline -> smoothing -> normalization
    if steps_settings['despike']:
        df, removed = processing.remove_spikes(df, steps_settings['despike'])
        spike_note.caption(t('Spike points replaced: {n}').format(n=sum(removed.values())))
    baselines = processing.baselines(df, *steps_settings['baseline']) if steps_settings['baseline']         else pd.DataFrame(0.0, index=df.index, columns=df.columns)
    corrected = df - baselines
    smoothed = processing.smooth(corrected, *steps_settings['smoothing']) if steps_settings['smoothing']         else corrected
    plot_df = smoothed
    if normalization != 'none':
        plot_df = processing.normalize_by(plot_df, normalization,
                                          peak=reference if normalization == 'peak' else None)

    # charts
    if chart_type == 'GS':
        if shift:
            step = shift * (plot_df.max().max() - plot_df.min().min())
            plot_df = plot_df + [i * step for i in range(plot_df.shape[1])]
        fig = px.line(plot_df, color_discrete_sequence=settings['palette'])

    elif chart_type == 'P3D':
        long = plot_df.reset_index().melt(plot_df.index.name, plot_df.columns)
        fig = px.line_3d(long, x='variable', y=plot_df.index.name, z='value', color='variable',
                         color_discrete_sequence=settings['palette'])
        fig.update_layout(scene_camera=dict(eye=dict(x=1.9, y=0.15, z=0.2)), height=800)

    elif processed and show_steps:
        name = df.columns[0]
        parts = {name: df[name]}
        if steps_settings['baseline']:
            parts[t('Baseline')] = baselines[name]
            parts[t('Baseline corrected')] = corrected[name]
        if steps_settings['smoothing']:
            parts[t('Smoothed')] = smoothed[name]
        steps = pd.DataFrame(parts)
        fig = px.line(steps, color_discrete_sequence=settings['palette'])
        plot_df = steps

    else:
        fig = px.line(plot_df, color_discrete_sequence=settings['palette'])

    if show_peaks:
        # peaks of the displayed spectra (in the steps view - of the final, processed spectrum)
        peak_source = plot_df.iloc[:, [-1]] if chart_type in {'SINGLE', 'MS'} and processed and show_steps else plot_df
        peaks_table = peaks.find_peaks_all(peak_source, **peak_options)
        colors = {trace.name: trace.line.color for trace in fig.data}
        labelled = peaks.label_once(peaks_table, tolerance=max(3, peak_options['min_distance'] / 2))
        for spectrum, group in peaks_table.groupby('spectrum', sort=False):
            fig.add_trace(go.Scatter(x=group['position'], y=group['intensity'], mode='markers+text',
                                     text=[f'{p:.0f}' if labelled[i] else '' for i, p in group['position'].items()],
                                     textposition='top center',
                                     textfont=dict(size=11, color=colors.get(spectrum)),
                                     marker=dict(symbol='triangle-down', size=8, color=colors.get(spectrum)),
                                     showlegend=False, hovertemplate='%{x:.1f} cm⁻¹<extra></extra>'))

    chart_options = {}
    if normalization == 'peak' and chart_type != 'P3D':
        # reference peak highlighted like the peak ranges on other pages; it can be selected on the chart
        vis_utils.highlight_range(fig, *reference)
        fig.update_layout(dragmode='select', selectdirection='h')
        chart_options = dict(key='vis_chart', selection_mode='box',
                             on_select=lambda: vis_utils.range_from_selection('vis_chart', 'reference_peak',
                                                                              *reference_limits))

    with chart_col:
        vis_utils.show_chart(fig, settings, lines=chart_type != 'P3D', **chart_options)
        vis_utils.download_csv(plot_df.reset_index(), 'spectra.csv', t('Download data (CSV)'), 'vis_csv',
                               index=False)
        if show_peaks:
            st.subheader(t('Peaks'))
            table = peaks_table.rename(columns={'spectrum': t('Spectrum'), 'position': t('Raman Shift [cm⁻¹]'),
                                                'intensity': t('Intensity'), 'prominence': t('Prominence'),
                                                'fwhm': t('FWHM [cm⁻¹]')})
            if chart_type == 'GS' and shift:
                st.caption(t('Intensities include the separation shift of the chart.'))
            st.dataframe(table.style.format({t('Raman Shift [cm⁻¹]'): '{:.1f}', t('Intensity'): '{:.4g}',
                                             t('Prominence'): '{:.4g}', t('FWHM [cm⁻¹]'): '{:.1f}'}),
                         hide_index=True, width='stretch')
            vis_utils.download_csv(peaks_table, 'peaks.csv', t('Download peaks (CSV)'), 'peaks_csv', index=False)

        if chart_type != 'P3D':
            vis_utils.report_button(
                'visualisation',
                lambda: build_report(plot_df, chart_type, steps_settings, normalization,
                                     peaks_table if show_peaks else None),
                (chart_type, steps_settings, normalization, show_peaks, plot_df.shape, float(plot_df.to_numpy().sum())))


def build_report(plot_df, chart_type, steps_settings, normalization, peaks_table):
    from core import report

    rep = report.Report(t('Visualisation'))
    rep.heading(t('Data'))
    rep.key_values({t('Files'): ', '.join(workspace.file_names()) or '—', t('Chart type'): t(CHART_TYPES[chart_type]),
                    t('Spectra'): plot_df.shape[1],
                    t('Raman Shift range [cm⁻¹]'): f'{plot_df.index.min():.0f} – {plot_df.index.max():.0f}'})
    rep.heading(t('Processing'))
    baseline, smoothing = steps_settings['baseline'], steps_settings['smoothing']
    rep.key_values({
        t('Remove spikes (cosmic rays)'): steps_settings['despike'] or '—',
        t('Baseline correction'): f'{t(data_customisation.BASELINE_LABELS[baseline[0]])}, {baseline[1]}'
        if baseline else '—',
        t('Smoothing'): f'{t(data_customisation.SMOOTHING_LABELS[smoothing[0]])}, {smoothing[1]}' if smoothing else '—',
        t('Normalization'): t(NORMALIZATIONS[normalization])})
    rep.figure(report.spectra_figure(plot_df))
    if peaks_table is not None and not peaks_table.empty:
        rep.heading(t('Peaks'))
        rep.table(peaks_table.rename(columns={'spectrum': t('Spectrum'), 'position': 'cm⁻¹',
                                              'intensity': t('Intensity'), 'prominence': t('Prominence'),
                                              'fwhm': 'FWHM'}), index=False)
    return rep.to_bytes()
