import pandas as pd
import plotly.express as px
import streamlit as st

from core import processing
from vis_helpers import manual, data_customisation, vis_utils
from vis_helpers.i18n import t, choice

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
        chart_type = choice('selectbox', t('Chart type'), list(CHART_TYPES), key='chart_type',
                            format_func=lambda c: t(CHART_TYPES[c]))
        if chart_type == 'SINGLE':
            df = df[[st.selectbox(t('Spectrum'), list(df.columns), key='single_spectrum')]]
        elif chart_type == 'MS':
            df = df.mean(axis=1).rename(t('Average')).to_frame()

        with st.expander(t('Range'), icon=':material/straighten:'):
            df = vis_utils.trim_spectra(df)
            if chart_type == 'GS':
                shift = st.slider(t('Separate spectra from each other'), 0.0, 1.0, 0.0, 0.05, key='shift')

        with st.expander(t('Processing'), icon=':material/tune:', expanded=True):
            processed = st.checkbox(t('Baseline correction and smoothing'), key='processed')
            if processed:
                params = data_customisation.processing_params(df.columns, allow_each=chart_type in {'GS', 'P3D'})
                show_steps = chart_type in {'SINGLE', 'MS'} and st.checkbox(
                    t('Show baseline and intermediate steps'), key='show_steps')
            normalized = st.checkbox(t('Normalize (0-1)'), key='normalized')

        with st.expander(t('Chart appearance'), icon=':material/palette:'):
            settings = vis_utils.chart_settings('vis')

    # processing
    plot_df = df
    if processed:
        baselines, corrected, smoothed = processing.baseline_and_smooth(df, params)
        plot_df = smoothed
    if normalized:
        plot_df = processing.normalize(plot_df)

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
        steps = pd.concat([df[name], baselines[name], corrected[name], smoothed[name]], axis=1,
                          keys=[name, t('Baseline'), t('Baseline corrected'), t('Baseline corrected + smoothed')])
        fig = px.line(steps, color_discrete_sequence=settings['palette'])
        plot_df = steps

    else:
        fig = px.line(plot_df, color_discrete_sequence=settings['palette'])

    with chart_col:
        vis_utils.show_chart(fig, settings, lines=chart_type != 'P3D')
        vis_utils.download_csv(plot_df.reset_index(), 'spectra.csv', t('Download data (CSV)'), 'vis_csv',
                               index=False)
