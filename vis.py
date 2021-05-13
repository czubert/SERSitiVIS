

import pandas as pd
import peakutils
import plotly.express as px
import streamlit as st

import authors
from constants import LABELS
from for_streamlit_only import manual, sidebar, data_customisation, charts
from processing import utils
from processing.save_read import read_files
from visualisation import draw
from visualisation import visualisation_options as vis_opt


def main():
    sidebar.sidebar_head()

    st.sidebar.write('#### Choose spectra type', unsafe_allow_html=True)
    spectrometer = st.sidebar.radio(
        "",
        (LABELS['BWTEK'], LABELS['RENI'], LABELS['WITEC'], LABELS['WASATCH'], LABELS['TELEDYNE']),
        index=0)

    # users data loader
    st.sidebar.write('#### Upload your data', unsafe_allow_html=True)
    files = st.sidebar.file_uploader(label='', accept_multiple_files=True, type=['txt', 'csv'])

    # allow example data loading when no custom data are loaded
    if not files:
        st.sidebar.write('#### Or try with our', unsafe_allow_html=True)
        if st.sidebar.checkbox("Load example data"):
            files = utils.load_example_files(spectrometer)

    if files:
        df = read_files(spectrometer, files)

        # choose plot colors and tamplates
        with st.beta_expander("Customize your chart"):
            plots_color, template = draw.choosing_colorway(), draw.choose_template()

        # lets you select chart type
        chart_type = vis_opt.vis_options(spectrometer)

        # lets you select data conversion type
        spectra_conversion_type = vis_opt.convertion_opt()

        # TODO need improvements
        # getting rid of duplicated columns
        df = df.loc[:, ~df.columns.duplicated()]

        #
        # # data manipulation - raw / optimization / normalization
        #
        if spectra_conversion_type == LABELS["NORM"]:
            df = (df - df.min()) / (df.max() - df.min())

        if chart_type == LABELS['MS']:
            df = df.mean(axis=1).rename('Average').to_frame()

        # For grouped spectra sometimes we want to shift the spectra from each other, here it is:
        if chart_type == LABELS['GS']:
            shift = data_customisation.get_shifting_distance(spectra_conversion_type)
        else:
            shift = None

        # every chart (or pair) gets its own columns
        tmp_cols = [st.beta_columns([5, 2]) for _ in df.columns]
        cols_left, cols_right = zip(*tmp_cols)
        vals = data_customisation.get_deg_win(chart_type, spectra_conversion_type, cols_right, df.columns)

        # data conversion and
        if spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]}:
            baselines = pd.DataFrame(index=df.index)
            baselined = pd.DataFrame(index=df.index)
            flattened = pd.DataFrame(index=df.index)
            for col in df.columns:
                baselines[col] = peakutils.baseline(df[col], vals[col][0])
                baselined[col] = df[col] - baselines[col]
                flattened[col] = baselined[col].rolling(window=vals[col][1], min_periods=1, center=True).mean()

        #
        # # plotting
        #
        if chart_type == LABELS['GS']:
            shifters = [(i + 1) * shift for i in range(len(df.columns))]
            df_plot = df if spectra_conversion_type == LABELS["RAW"] else flattened
            df_plot = df_plot + shifters

            figs = [px.line(df_plot, x=df_plot.index, y=df_plot.columns, color_discrete_sequence=plots_color)]

        elif chart_type == LABELS['MS']:
            if spectra_conversion_type == LABELS["RAW"]:
                figs = [px.line(df, x=df.index, y=df.columns, color_discrete_sequence=plots_color)]

            elif spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]}:
                columns = ['Average', 'Baseline', 'BL-Corrected', 'Flattened + BL-Corrected']
                plot_df = pd.concat([df, baselines, baselined, flattened], axis=1)
                plot_df.columns = columns

                fig1 = px.line(plot_df, x=plot_df.index, y=columns[-1], color_discrete_sequence=plots_color[3:])
                fig2 = px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)
                figs = [(fig1, fig2)]
            else:
                raise ValueError('Unknown conversion type for Mean spectrum chart')

        elif chart_type == LABELS['P3D']:
            df3d = flattened if spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]} else df

            df3d = df3d.reset_index().melt('Raman Shift', df3d.columns)
            fig = px.line_3d(df3d, x='variable', y='Raman Shift', z='value', color='variable')

            camera = dict(eye=dict(x=1.9, y=0.15, z=0.2))
            fig.update_layout(scene_camera=camera,
                              width=1200, height=1200,
                              margin=dict(l=1, r=1, t=30, b=1),
                              )
            figs = [fig]

        elif chart_type == LABELS['SINGLE']:
            if spectra_conversion_type == LABELS["RAW"]:
                figs = [px.line(df[col], color_discrete_sequence=plots_color) for col in df.columns]
            else:
                columns = ['Average', 'Baseline', 'BL-Corrected', 'Flattened + BL-Corrected']
                figs = []
                for col_left, col in zip(cols_left, df.columns):
                    plot_df = pd.concat([df[col], baselines[col], baselined[col], flattened[col]], axis=1)
                    plot_df.columns = columns

                    fig1 = px.line(plot_df, x=plot_df.index, y=columns[-1],
                                   color_discrete_sequence=plots_color[3:])  # trick for color consistency
                    fig2 = px.line(plot_df, x=plot_df.index, y=plot_df.columns,
                                   color_discrete_sequence=plots_color)
                    fig_tup = (fig1, fig2)
                    figs.append(fig_tup)
        else:
            raise ValueError("Something unbelievable has been chosen")

        charts.show_charts(cols_left, figs, plots_color, template)
    else:
        manual.show_manual()

    authors.show_developers()





if __name__ == '__main__':
    main()
    print("Streamlit finished it's work")
