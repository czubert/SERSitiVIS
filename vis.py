import io

import pandas as pd
import peakutils
import plotly.express as px
import streamlit as st
import os
import datetime
# noinspection PyUnresolvedReferences
import str_slider
from constants import LABELS
from processing import utils
from vis_helpers import manual, sidebar, data_customisation, charts, authors, vis_utils
from vis_helpers.vis_utils import print_widgets_separator
from visualisation import visualisation_options as vis_opt


def main():
    """
    Main is responsible for the visualisation of everything connected with streamlit.
    It is the web application itself.
    """

    # # Radiobuttons in one row
    # st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

    # Sets sidebar's header and logo
    sidebar.sidebar_head()

    analysis_type = st.sidebar.selectbox("Analysis type", ['visualisation', 'PCA', 'EF', 'RMSE'])
    if analysis_type == 'visualisation':
        visualisation()
    elif analysis_type == 'PCA':
        pca.main()
    elif analysis_type == 'EF':
        enhancement_factor.main()
    elif analysis_type == 'RMSE':
        rmse.main()
    authors.show_developers()


def visualisation():
    #
    # # Spectrometer type `- BWTek / Renishaw / Witec / Wasatch / Teledyne
    #
    spectra_types = ['EMPTY', 'BWTEK', 'RENI', 'WITEC', 'WASATCH', 'TELEDYNE', 'JOBIN']
    spectrometer = st.sidebar.selectbox(
        "Spectra type",
        spectra_types,
        format_func=LABELS.get,
        index=0)

    # sidebar separating line
    print_widgets_separator(1, sidebar=True)

    # User data loader
    # sidebar.print_widget_labels('Upload your data or try with ours', 10, 0)

    files = st.sidebar.file_uploader(label='Upload your data or try with ours',
                                     accept_multiple_files=True,
                                     type=['txt', 'csv'])

    # Allow example data loading when no custom data are loaded
    if not files and st.sidebar.checkbox("Load example data"):
        if spectrometer == "EMPTY":
            st.sidebar.error('First Choose Spectra type')
        else:
            files = utils.load_example_files(spectrometer)

    # Check if data loaded, if yes, perform actions
    if files:
        st.spinner('Uploading data in progress')
        # sidebar separating line
        print_widgets_separator(1, sidebar=True)
        df = files_to_df(files, spectrometer)
        # Select chart type
        chart_type = vis_opt.vis_options()

        # sidebar separating line
        print_widgets_separator(1, sidebar=True)

        # Select data conversion type
        spectra_conversion_type = vis_opt.convertion_opt()

        # TODO need improvements
        # getting rid of duplicated columns
        df = df.loc[:, ~df.columns.duplicated()]

        #
        # # data manipulation - raw / optimization / normalization
        #

        # TODO delete if not needed
        # Normalization
        # if spectra_conversion_type == LABELS["NORM"]:
        #     df = (df - df.min()) / (df.max() - df.min())

        # Mean Spectra
        if chart_type == 'MS':
            df = df.mean(axis=1).rename('Average').to_frame()

        # columns in main view. Chart, expanders
        # TODO rozwiązać to jakoś sprytniej

        col_left, col_right = st.beta_columns([5, 2])

        if chart_type == 'SINGLE':
            with col_left:
                col = st.selectbox('', df.columns)
                df = df[[col]]

        with col_right:
            normalized = False

            # # Plot settings
            plot_settings = st.beta_expander("Plot settings", expanded=False)

            # # Choose plot colors and templates
            with plot_settings:
                plots_color, template = vis_utils.get_chart_vis_properties_vis()
                vis_utils.print_widget_labels('Labels')
                xaxis = st.text_input('X axis name', r'Raman Shift cm <sup>-1</sup>')
                yaxis = st.text_input('Y axis name', r'Intensity [au]')
                title = st.text_input('Title', r'')
                chart_titles = {'x': xaxis, 'y': yaxis, 'title': title}

            # # Range and separation
            range_expander_name = 'Range' if chart_type in {'SINGLE', 'MS'} else 'Range and separation'
            range_expander = st.beta_expander(range_expander_name, expanded=False)

            with range_expander:
                df = vis_utils.trim_spectra(df)

            if spectra_conversion_type != "RAW":

                # # Data Manipulation
                with st.beta_expander("Data Manipulation", expanded=False):
                    vals = data_customisation.get_deg_win(chart_type, spectra_conversion_type, df.columns)

                    normalized = st.checkbox("Normalize")
                    if normalized:
                        df = (df - df.min()) / (df.max() - df.min())

        # data conversion end
        if spectra_conversion_type == 'OPT':
            baselines = pd.DataFrame(index=df.index)
            baselined = pd.DataFrame(index=df.index)
            flattened = pd.DataFrame(index=df.index)
            for col in df.columns:
                tmp_spectrum = df[col].dropna()  # trick for data with NaNs
                tmp_spectrum = pd.Series(peakutils.baseline(tmp_spectrum, vals[col][0]), index=tmp_spectrum.index)
                baselines[col] = tmp_spectrum

                baselined[col] = df[col] - baselines[col]
                flattened[col] = baselined[col].rolling(window=vals[col][1], min_periods=1, center=True).mean()
        #
        # # Plotting
        #

        # Groupped spectra
        if chart_type == 'GS':
            with range_expander:
                shift = data_customisation.separate_spectra(normalized)

                shifters = [(i + 1) * shift for i in range(len(df.columns))]
                plot_df = df if spectra_conversion_type == 'RAW' else flattened
                plot_df = plot_df + shifters
                figs = [px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)]

        # Mean spectra
        elif chart_type == 'MS':
            if spectra_conversion_type == 'RAW':
                plot_df = df
                figs = [px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)]

            elif spectra_conversion_type == 'OPT':
                columns = ['Average', 'Baseline', 'BL-Corrected', 'Flattened + BL-Corrected']
                plot_df = pd.concat([df, baselines, baselined, flattened], axis=1)
                plot_df.columns = columns

                fig1 = px.line(plot_df, x=plot_df.index, y=columns[-1], color_discrete_sequence=plots_color[3:])
                fig2 = px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)
                figs = [(fig1, fig2)]
            else:
                raise ValueError('Unknown conversion type for Mean spectrum chart')
        # 3D spectra
        elif chart_type == 'P3D':
            plot_df = flattened if spectra_conversion_type in {"OPT"} else df

            plot_df = plot_df.reset_index().melt('Raman Shift', plot_df.columns)
            fig = px.line_3d(plot_df, x='variable', y='Raman Shift', z='value', color='variable')

            camera = dict(eye=dict(x=1.9, y=0.15, z=0.2))
            fig.update_layout(scene_camera=camera,
                              width=1200, height=1200,
                              margin=dict(l=1, r=1, t=30, b=1),
                              )
            figs = [fig]

        # Single spectra
        elif chart_type == 'SINGLE':
            if spectra_conversion_type == 'RAW':
                plot_df = df
                figs = [px.line(plot_df[col], color_discrete_sequence=plots_color) for col in plot_df.columns]
            else:
                columns = ['Average', 'Baseline', 'BL-Corrected', 'Flattened + BL-Corrected']
                figs = []

                plot_df = pd.concat([df, baselines, baselined, flattened], axis=1)
                plot_df.columns = columns

                fig1 = px.line(plot_df, x=plot_df.index, y=columns[-1],
                               color_discrete_sequence=plots_color[3:])  # trick for color consistency
                fig2 = px.line(plot_df, x=plot_df.index, y=plot_df.columns,
                               color_discrete_sequence=plots_color)
                fig_tup = (fig1, fig2)
                figs.append(fig_tup)
        else:
            raise ValueError("Something unbelievable has been chosen")

        with col_left:
            charts.show_charts(figs, plots_color, chart_titles, template)

        with col_left:
            st.markdown('')
            link = utils.download_button(plot_df.reset_index(), f'spectrum.csv',
                                         button_text='Download CSV')
            st.markdown(link, unsafe_allow_html=True)

    else:
        manual.show_manual()

    authors.show_developers()


if __name__ == '__main__':
    # try:
    #     import streamlit_analytics
    #
    #     credential_file = 'tmp_credentials.json'
    #     if not os.path.exists(credential_file):
    #         with open(credential_file, 'w') as infile:
    #             infile.write(st.secrets['firebase_credentials'])
    #         print('credentials written')
    #
    #     collection = datetime.date.today().strftime("%Y-%m")
    #     with streamlit_analytics.track(firestore_key_file=credential_file,
    #                                    firestore_collection_name=collection,
    #                                    # verbose=True
    #                                    ):
    #         main()
    # except KeyError:
    #     main()

    main()

    print("Streamlit finished it's work")
