import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import analysis, calibration, maps, processing
from vis_helpers import background, data_customisation, vis_utils, workspace
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

    data_id = (tuple(df.columns), *vis_utils.spectrum_limits(df))
    if st.session_state.get(DATA_KEY) != data_id:  # new data -> start again from the strongest peak
        st.session_state[DATA_KEY] = data_id
        st.session_state.pop(RANGE_KEY, None)
    all_df, df = df, background.samples(df)
    if df.shape[1] < 4:
        st.warning(t('A map needs at least 4 spectra.'))
        background.panel_if_hidden(all_df, df)
        return

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
        df, subtraction = background.subtract(df, background.panel(all_df))
        low, high = vis_utils.spectrum_limits(df)
        peak_range = vis_utils.range_slider(t('Peak range'), low, high, key=RANGE_KEY,
                                            default=calibration.strongest_peak_range(df))
        method = choice('radio', t('Signal'), ['height', 'area'], key='map_method', horizontal=True,
                        format_func=lambda m: t('Peak height') if m == 'height' else t('Peak area'))
    with chart_col:
        mode, half_window = data_customisation.peak_baseline_switch('map')
    baseline_text = data_customisation.describe_peak_baseline(mode, half_window)

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
    vis_utils.highlight_range(fig, *peak_range)
    if mode != 'none' and len(processing.trim(df, *peak_range)) >= 3:  # baseline under the mean spectrum
        _, mean_base = analysis.peak_window(mean.to_frame(), *peak_range, mode, half_window)
        fig.add_trace(go.Scatter(x=mean_base.index, y=mean_base.iloc[:, 0], mode='lines', showlegend=False,
                                 hoverinfo='skip', line=dict(dash='dot', width=2, color=palette[0])))
    with chart_col:
        st.caption(t('Tip: drag on the chart to select the peak range.'))
        vis_utils.show_chart(fig, vis_utils.default_chart_settings(), lines=False, key=CHART_KEY,
                             selection_mode='box',
                             on_select=lambda: vis_utils.range_from_selection(CHART_KEY, RANGE_KEY, low, high))

    if len(processing.trim(df, *peak_range)) < 3:
        st.warning(t('Peak range is too narrow'))
        return
    values = map_values(df, tuple(peak_range), method, mode, half_window)
    stats = maps.uniformity(values)
    moran = maps.morans_i(values, coords)

    # # Step 2 - map
    st.subheader(f'2. {t("Map")}')
    c = st.columns(6)
    c[0].metric('RSD', f'{stats["rsd"]:.1f} %', border=True,
                help=vis_utils.rsd_interval(stats['rsd'] / 100, stats['n']))
    c[1].metric(t('Mean'), number(stats['mean']), border=True)
    c[2].metric('Min', number(stats['min']), border=True)
    c[3].metric('Max', number(stats['max']), border=True)
    c[4].metric(t('Within ±20 % of mean'), f'{stats["within_20"]:.0f} %', border=True)
    c[5].metric(t('Points'), stats['n'], border=True)

    if moran:
        show_moran(moran)

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
    vis_utils.report_button('map', lambda: build_report(df, peak_range, method, baseline_text, stats, image, unit,
                                                        values, subtraction, moran),
                            (peak_range, method, baseline_text, relative, tuple(df.columns[:5]), float(values.sum()),
                             background.describe(subtraction)))


@st.cache_data(show_spinner=False, max_entries=8)
def map_values(df, peak_range, method, mode, half_window):
    """Peak signal of every map point - cached, a map can have thousands of spectra"""
    return calibration.peak_signal(df, *peak_range, method=method, mode=mode, half_window=half_window)


MORAN_TEXTS = {
    'clustered': "Moran's I = {i} (p = {p}): neighbouring points resemble each other - the differences form patches "
                 "or a gradient, e.g. uneven deposition. Look at the map for weaker areas.",
    'alternating': "Moran's I = {i} (p = {p}): neighbouring points differ more than by chance - check the order of "
                   "the points (snake order) and the stage.",
    'random': "Moran's I = {i} (p = {p}): the differences between points look random - no gradient or patches.",
}


def moran_pattern(moran):
    if moran['p'] >= 0.05:
        return 'random'
    return 'clustered' if moran['i'] > moran['expected'] else 'alternating'


def show_moran(moran):
    """Is the non-uniformity random, or a gradient / patches? (Moran's I with a permutation test)"""
    pattern = moran_pattern(moran)
    text = t(MORAN_TEXTS[pattern]).format(i=f'{moran["i"]:.2f}', p=f'{moran["p"]:.3f}')
    help_text = t("Same RSD, different substrate: scattered weak points (random) are noise, a weaker edge or patch "
                  "(clustered) points to the production process. p = how often a random shuffle of the same values "
                  "over the map looks at least as clustered.")
    if pattern == 'random':
        st.info(text, icon=':material/blur_on:')
    else:
        st.warning(text, icon=':material/gradient:')
    st.caption(help_text)


def build_report(df, peak_range, method, baseline_text, stats, image, unit, values, subtraction=None, moran=None):
    from core import report

    rep = report.Report(t('Substrate uniformity map'))
    rep.heading(t('Data'))
    rep.key_values({t('Files'): ', '.join(workspace.file_names()) or '—', t('Points'): stats['n'],
                    t('Subtract substrate background'): background.describe(subtraction),
                    t('Peak range'): f'{peak_range[0]} – {peak_range[1]} cm⁻¹',
                    t('Signal'): t('Peak height') if method == 'height' else t('Peak area'),
                    t('Baseline under the peak'): baseline_text})
    rep.heading(t('Results'))
    results = {'RSD': f'{stats["rsd"]:.1f} % ({vis_utils.rsd_interval(stats["rsd"] / 100, stats["n"])})',
               t('Mean'): number(stats['mean']), 'Min': number(stats['min']), 'Max': number(stats['max']),
               t('Within ±20 % of mean'): f'{stats["within_20"]:.0f} %'}
    if moran:
        results["Moran's I"] = t(MORAN_TEXTS[moran_pattern(moran)]).format(i=f'{moran["i"]:.2f}',
                                                                          p=f'{moran["p"]:.3f}')
    rep.key_values(results)
    rep.figure(report.heatmap_figure(image, unit), width=140)
    rep.figure(report.histogram_figure(values, unit), width=120)
    return rep.to_bytes()
