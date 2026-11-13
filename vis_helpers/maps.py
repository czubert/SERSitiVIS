import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import calibration, maps, processing
from vis_helpers import vis_utils, workspace
from vis_helpers.i18n import t, choice

CHART_KEY = 'map_chart'
RANGE_KEY = 'map_range'
DATA_KEY = '_map_data'


def number(value):
    """10280 instead of 1.028e+04"""
    if abs(value) >= 1000:
        return f'{value:,.0f}'.replace(',', ' ')
    return f'{value:.3g}'


def main(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    st.header(t('Substrate uniformity map'))

    if df is None:
        st.warning(t('Upload spectra in the sidebar (or choose example data)'))
        st.info(t('Upload a map file (columns: X, Y, Raman Shift, Intensity - e.g. Renishaw WiRE export) or several '
                  'spectra measured on a regular grid.'))
        return

    if df.shape[1] < 4:
        st.warning(t('A map needs at least 4 spectra.'))
        return

    low, high = vis_utils.spectrum_limits(df)
    data_id = (tuple(df.columns), low, high)
    if st.session_state.get(DATA_KEY) != data_id:  # new data -> start again from the strongest peak
        st.session_state[DATA_KEY] = data_id
        st.session_state.pop(RANGE_KEY, None)

    # # Coordinates: from the map file, or a grid set by the user
    coords = maps.coordinates_from_names(df.columns)
    if coords is None:
        with st.container(border=True):
            st.markdown(f'**{t("Measurement grid")}**')
            st.caption(t('Spectra are placed on the grid row by row, in the order of the files.'))
            c = st.columns(4)
            n = df.shape[1]
            columns = c[0].number_input(t('Points in a row'), 1, n, int(np.ceil(np.sqrt(n))), key='map_columns')
            step_x = c[1].number_input(t('Step X [µm]'), 0.01, 10000.0, 1.0, key='map_step_x')
            step_y = c[2].number_input(t('Step Y [µm]'), 0.01, 10000.0, 1.0, key='map_step_y')
            snake = c[3].checkbox(t('Snake order'), key='map_snake',
                                  help=t('Every second row measured in the opposite direction.'))
            if n % columns:
                st.caption(t('{n} spectra do not fill the last row - it stays partly empty.').format(n=n))
        coords = maps.grid_coordinates(df.columns, int(columns), step_x, step_y, snake)

    # # Step 1 - peak
    st.subheader(f'1. {t("Peak")}')
    chart_col, settings_col = st.columns((3, 1))
    with settings_col:
        peak_range = vis_utils.range_slider(t('Peak range'), low, high, key=RANGE_KEY,
                                            default=calibration.strongest_peak_range(df))
        method = choice('radio', t('Signal'), ['height', 'area'], key='map_method', horizontal=True,
                        format_func=lambda m: t('Peak height') if m == 'height' else t('Peak area'))
        degree = st.slider(t('Polynomial degree for baseline correction'), 0, 5, 1, key='map_degree',
                           help=t('Baseline is fitted within the peak range'))

    # mean spectrum with min-max band - lighter than drawing hundreds of spectra
    mean, lowest, highest = df.mean(axis=1), df.min(axis=1), df.max(axis=1)
    palette = vis_utils.sersitive_palette()
    fig = go.Figure([
        go.Scatter(x=df.index, y=highest, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'),
        go.Scatter(x=df.index, y=lowest, mode='lines', line=dict(width=0), fill='tonexty',
                   fillcolor='rgba(108, 155, 192, 0.3)', name=t('Min – max')),
        go.Scatter(x=df.index, y=mean, mode='lines', line=dict(color=palette[0]), name=t('Mean spectrum')),
    ])
    fig.update_layout(dragmode='select', selectdirection='h', height=360)
    fig.add_vrect(x0=peak_range[0], x1=peak_range[1], line_width=0, fillcolor='gold', opacity=0.25)
    with chart_col:
        st.caption(t('Tip: drag on the chart to select the peak range.'))
        vis_utils.show_chart(fig, vis_utils.default_chart_settings(), lines=False, key=CHART_KEY,
                             selection_mode='box',
                             on_select=lambda: vis_utils.range_from_selection(CHART_KEY, RANGE_KEY, low, high))

    if len(processing.trim(df, *peak_range)) < 3:
        st.warning(t('Peak range is too narrow'))
        return
    values = calibration.peak_signal(df, *peak_range, method=method, degree=degree)
    stats = maps.uniformity(values)

    # # Step 2 - map
    st.subheader(f'2. {t("Map")}')
    c = st.columns(6)
    c[0].metric('RSD', f'{stats["rsd"]:.1f} %', border=True)
    c[1].metric(t('Mean'), number(stats['mean']), border=True)
    c[2].metric('Min', number(stats['min']), border=True)
    c[3].metric('Max', number(stats['max']), border=True)
    c[4].metric(t('Within ±20 % of mean'), f'{stats["within_20"]:.0f} %', border=True)
    c[5].metric(t('Points'), stats['n'], border=True)

    map_col, options_col = st.columns((3, 1))
    with options_col:
        relative = st.checkbox(t('Show as % of mean'), key='map_relative')
        scale = st.selectbox(t('Colour scale'), ['Viridis', 'Cividis', 'Plasma', 'Blues', 'RdBu_r'], key='map_scale')

    image = maps.grid(100 * values / stats['mean'] if relative else values, coords)
    unit = '%' if relative else (t('Peak height') if method == 'height' else t('Peak area'))
    heatmap = px.imshow(image, origin='lower', aspect='equal', color_continuous_scale=scale,
                        labels=dict(x='X [µm]', y='Y [µm]', color=unit))
    heatmap.update_layout(height=520, margin=dict(t=30))
    with map_col:
        config = {'displaylogo': False, 'toImageButtonOptions': {'format': 'png', 'scale': 3, 'filename': 'map'}}
        st.plotly_chart(heatmap, width='stretch', config=config)

    with options_col:
        histogram = px.histogram(values, nbins=min(30, max(5, stats['n'] // 3)),
                                 color_discrete_sequence=[palette[1]])
        histogram.update_layout(height=260, showlegend=False, margin=dict(l=10, r=10, t=30, b=10),
                                xaxis_title=unit, yaxis_title=t('Points'), title=dict(text=t('Distribution')))
        st.plotly_chart(histogram, width='stretch', config={'displaylogo': False})

    export = coords.assign(value=values.reindex(coords.index)).rename_axis(t('Spectrum')).reset_index()
    vis_utils.download_csv(export, 'map.csv', t('Download map (CSV)'), 'map_csv', index=False)
    vis_utils.report_button('map', lambda: build_report(df, peak_range, method, degree, stats, image, unit, values),
                            (peak_range, method, degree, relative, tuple(df.columns[:5]), float(values.sum())))


def build_report(df, peak_range, method, degree, stats, image, unit, values):
    from core import report

    rep = report.Report(t('Substrate uniformity map'))
    rep.heading(t('Data'))
    rep.key_values({t('Files'): ', '.join(workspace.file_names()) or '—', t('Points'): stats['n'],
                    t('Peak range'): f'{peak_range[0]} – {peak_range[1]} cm⁻¹',
                    t('Signal'): t('Peak height') if method == 'height' else t('Peak area'),
                    t('Polynomial degree for baseline correction'): degree})
    rep.heading(t('Results'))
    rep.key_values({'RSD': f'{stats["rsd"]:.1f} %', t('Mean'): number(stats['mean']), 'Min': number(stats['min']),
                    'Max': number(stats['max']), t('Within ±20 % of mean'): f'{stats["within_20"]:.0f} %'})
    rep.figure(report.heatmap_figure(image, unit), width=140)
    rep.figure(report.histogram_figure(values, unit), width=120)
    return rep.to_bytes()
