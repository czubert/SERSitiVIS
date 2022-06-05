import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.preprocessing import MinMaxScaler

import processing
from constants import LABELS
from . import rsd_utils, sidebar, vis_utils
from visualisation.draw import fig_layout

SLIDERS_PARAMS_RAW = {'rel_height': dict(min_value=1, max_value=100, value=20, step=1),
                      'height': dict(min_value=1000, max_value=100000, value=10000, step=1000),
                      }
SLIDERS_PARAMS_NORMALIZED = {'rel_height': dict(min_value=0.01, max_value=1., value=0.5, step=0.01),
                             'height': dict(min_value=0.001, max_value=1., value=0.1, step=0.001),
                             }


# TODO sprawdzić jak liczą w publikacjach RSD, czy to chodzi o różnice intensywnosci miedzy widmami,
#  czy o stosunek pików, który w sumie powinien być stały... więc trochę bez sensu

def main():
    rsd_types = ['OneP', 'P2P']
    st.header('Relative Standard Deviation (RSD)')

    spectrometer = sidebar.choose_spectra_type()

    vis_utils.print_widgets_separator(sidebar=True)

    files = st.sidebar.file_uploader(label='Upload your data or try with ours',
                                     accept_multiple_files=True,
                                     type=['txt', 'csv'])

    if not files:
        return st.warning("Upload data for calculatios")

    main_expander = st.expander("Customize your chart")
    # Choose plot colors and templates
    with main_expander:
        plot_palette, plot_template = vis_utils.get_chart_vis_properties()
    
    rsd_type = st.radio("RSD type:",
                        rsd_types,
                        format_func=LABELS.get,
                        index=0)
    if len(files) == 1:
        return st.warning('Upload more than one spectrum')
    df = processing.save_read.files_to_df(files, spectrometer)
    df = df.interpolate().bfill().ffill()

    plot_x_min = int(df.index.min())
    plot_x_max = int(df.index.max())

    rescale = st.sidebar.checkbox("Normalize")

    # FIX why slider_params is not used?
    if rescale:
        scaler = MinMaxScaler()
        rescaled_data = scaler.fit_transform(df)
        df = pd.DataFrame(rescaled_data, columns=df.columns, index=df.index)
        sliders_params = SLIDERS_PARAMS_NORMALIZED
    else:
        sliders_params = SLIDERS_PARAMS_RAW

    bg_colors = {'Peak 1': 'yellow', 'Peak 2': 'green'}

    cols = st.columns((0.6, 5.5, 3.5))
    with cols[1]:
        peak1_range = st.slider(f'Peak 1 range ({bg_colors["Peak 1"]})',
                                min_value=plot_x_min,
                                max_value=plot_x_max,
                                value=[plot_x_min, plot_x_max])

    with cols[1]:
        if rsd_type == 'P2P':
            peak2_range = st.slider(f'Peak 2 range ({bg_colors["Peak 2"]})',
                                    min_value=plot_x_min,
                                    max_value=plot_x_max,
                                    value=[plot_x_min, plot_x_max])
    
    fig = px.line(df)
    fig_layout(plot_template, fig, plots_colorscale=plot_palette)
    fig.update_xaxes(range=[plot_x_min, plot_x_max])

    peaks = zip([peak1_range], ['Peak 1'])
    
    if rsd_type == 'P2P':
        peaks = zip([peak1_range, peak2_range], ['Peak 1', 'Peak 2'])

    for ran, text in peaks:
        if ran == [plot_x_min, plot_x_max]: continue

        fig.add_vline(x=ran[0], line_dash="dash", annotation_text=text)
        fig.add_vline(x=ran[1], line_dash="dash")
        fig.add_vrect(x0=ran[0], x1=ran[1], line_width=0, fillcolor=bg_colors[text], opacity=0.15)

    cols = st.columns((7, 3))

    with cols[0]:
        st.plotly_chart(fig, use_container_width=True)

    mask = (peak1_range[0] <= df.index) & (df.index <= peak1_range[1])

    peak1 = df[mask]
    
    if rsd_type == 'P2P':
        mask = (peak2_range[0] <= df.index) & (df.index <= peak2_range[1])
        peak2 = df[mask]

    with cols[1]:
        st.header('RSD scores')
        st.write(' ')
        degree = st.slider('Choose polynomial degree for baseline correcion', 0, 20, 3, 1)
        round_num = st.slider('Choose decimal places in results', 0, 4, 2, 1)
        if rsd_type == 'OneP':
            st.table(rsd_utils.rsd_one_peak(peak1, degree, round_num))
        elif rsd_type == 'P2P':
            st.table(rsd_utils.rsd_peak_to_peak_ratio(peak1, peak2, degree, round_num))

    # TODO to bym przerzucił do wizualizacji i jakoś zaaplikował możliwość dodania peaków do widma
    # cols = st.columns(4)
    # peak_width = cols[0].slider('Min width', min_value=5, max_value=100, value=15, step=5, )
    # peak_distance = cols[1].slider('Min distance', min_value=1, max_value=100, value=5, step=1, )
    # peak_rel_height = cols[2].slider('Min relative height', **sliders_params['rel_height'])
    # peak_height = cols[3].slider('Min absolute height', **sliders_params['height'])
    #
    # peak_width = int(peak_width)
    # peak_distance = int(peak_distance)
    # peak_rel_height = float(peak_rel_height) if rescale else int(peak_rel_height)
    # peak_height = float(peak_height) if rescale else int(peak_height)
    #
    # peak_df = pd.DataFrame()
    # for col in df.columns:
    #     # TODO dodać opcję wyświetlania peaków na wykresach z podpisami od pasm dla maximow lokalnych
    #     #  oczywiście gdzieś w wersji wizualizacyjnej
    #     peaks = np.array(find_peaks(df[col], width=peak_width, distance=peak_distance,
    #                                 rel_height=peak_rel_height, height=peak_height)
    #                      )[0]
    #     peak_df = pd.concat([peak_df, df[col].reset_index().iloc[pd.Series(peaks), :].set_index('Raman Shift')],
    #                         axis=1)
