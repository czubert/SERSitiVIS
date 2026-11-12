import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from constants import LABELS
from core import analysis, processing
from . import vis_utils
from visualisation.draw import fig_layout


def main(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    rsd_types = ['OneP', 'P2P']
    st.header('Relative Standard Deviation (RSD)')

    if df is None:
        st.warning('Upload spectra in the sidebar (or choose example data)')
        return

    spectra = st.multiselect('Spectra', list(df.columns), default=list(df.columns), key='rsd_spectra')
    if len(spectra) < 2:
        st.warning('Choose at least two spectra')
        return
    df = df[spectra]

    with st.expander("Customize your chart"):
        plot_palette, plot_template = vis_utils.get_chart_vis_properties()

    rsd_type = st.radio("RSD type:", rsd_types, format_func=LABELS.get, index=0)

    plot_x_min = int(df.index.min())
    plot_x_max = int(df.index.max())

    # Normalisation only changes the chart. RSD measures differences in intensity between spectra,
    # normalising each spectrum to its maximum would remove them (RSD of the strongest peak = 0 %).
    normalized = st.sidebar.checkbox("Normalize chart", help='Changes only the chart - RSD is always calculated '
                                                             'from the original intensities')
    plot_df = processing.normalize(df) if normalized else df

    bg_colors = {'Peak 1': 'yellow', 'Peak 2': 'green'}

    cols = st.columns((0.6, 5.5, 3.5))
    with cols[1]:
        ranges = {'Peak 1': st.slider(f'Peak 1 range ({bg_colors["Peak 1"]})',
                                      min_value=plot_x_min, max_value=plot_x_max,
                                      value=(plot_x_min, plot_x_max))}
        if rsd_type == 'P2P':
            ranges['Peak 2'] = st.slider(f'Peak 2 range ({bg_colors["Peak 2"]})',
                                         min_value=plot_x_min, max_value=plot_x_max,
                                         value=(plot_x_min, plot_x_max))

    fig = px.line(plot_df, color_discrete_sequence=plot_palette)
    fig_layout(plot_template, fig, plots_colorscale=plot_palette)
    fig.update_xaxes(range=[plot_x_min, plot_x_max])

    for text, peak_range in ranges.items():
        if tuple(peak_range) == (plot_x_min, plot_x_max):
            continue
        fig.add_vline(x=peak_range[0], line_dash="dash", annotation_text=text)
        fig.add_vline(x=peak_range[1], line_dash="dash")
        fig.add_vrect(x0=peak_range[0], x1=peak_range[1], line_width=0, fillcolor=bg_colors[text], opacity=0.15)

    peaks = {name: processing.trim(df, *peak_range) for name, peak_range in ranges.items()}
    if any(len(peak) < 2 for peak in peaks.values()):
        st.warning('Peak range is too narrow')
        return

    cols = st.columns((7, 3))
    with cols[1]:
        st.header('RSD scores')
        st.write(' ')
        degree = st.slider('Polynomial degree for baseline correction', 0, 20, 1, 1, key='rsd_degree',
                           help='Baseline is fitted within each peak range - shown as dotted lines on the chart')
        round_num = st.slider('Choose decimal places in results', 0, 4, 2, 1)
        table = analysis.rsd_table(peaks['Peak 1'], peaks.get('Peak 2'), degree)
        st.table(table.style.format(f'{{:.{round_num}f}}'))

    # show baselines subtracted within peak ranges, so the effect of the polynomial degree is visible
    colors = {trace.name: trace.line.color for trace in fig.data}
    for peak_range in ranges.values():
        peak = processing.trim(plot_df, *peak_range)
        for spectrum in peak.columns:
            fig.add_trace(go.Scatter(x=peak.index, y=processing.baseline(peak[spectrum], degree, x=peak.index),
                                     mode='lines', line=dict(dash='dot', width=2, color=colors.get(spectrum)),
                                     name=f'{spectrum} - baseline', showlegend=False, hoverinfo='skip'))

    with cols[0]:
        st.plotly_chart(fig, width='stretch')
