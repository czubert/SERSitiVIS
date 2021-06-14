import datetime
import os

import pandas as pd
import peakutils
import plotly.express as px
import streamlit as st

# noinspection PyUnresolvedReferences
import str_slider
from constants import LABELS
from processing import save_read
from processing import utils
from vis_helpers import manual, sidebar, data_customisation, charts, authors, vis_utils
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

    #
    # # Spectrometer type `- BWTek / Renishaw / Witec / Wasatch / Teledyne
    #

    # sidebar.print_widget_labels('Choose spectra type')

    spectrometer = st.sidebar.selectbox(
        "Choose spectra type",
        ("None", LABELS['BWTEK'], LABELS['RENI'], LABELS['WITEC'], LABELS['WASATCH'], LABELS['TELEDYNE']),
        index=0)

    # sidebar separating line
    sidebar.print_widgets_separator()

    # User data loader
    # sidebar.print_widget_labels('Upload your data or try with ours', 10, 0)

    files = st.sidebar.file_uploader(label='Upload your data or try with ours',
                                     accept_multiple_files=True,
                                     type=['txt', 'csv'])

    # Allow example data loading when no custom data are loaded
    if not files:
        if st.sidebar.checkbox("Load example data"):
            if spectrometer == "None":
                st.sidebar.error('First Choose Spectra type')
            else:
                files = utils.load_example_files(spectrometer)

    # Check if data loaded, if yes, perform actions
    if files:
        st.spinner('Uploading data in progress')
        # sidebar separating line
        sidebar.print_widgets_separator()

        # df = save_read.read_files(spectrometer, files)
        try:
            df = save_read.read_files(spectrometer, files)
        except:
            st.error('Try choosing another type of spectra')
            st.stop()

        main_expander = st.beta_expander("Customize your chart")
        # Choose plot colors and templates
        with main_expander:
            plots_color, template = vis_utils.get_chart_vis_properties()

        # Select chart type
        chart_type = vis_opt.vis_options()

        # sidebar separating line
        sidebar.print_widgets_separator()

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
        normalized = False
        col_left, col_right = st.beta_columns([5, 2])
        if spectra_conversion_type != "RAW":
            col_right = col_right.beta_expander("Customize spectra", expanded=False)
            with col_right:
                vals = data_customisation.get_deg_win(chart_type, spectra_conversion_type, df.columns)
                if st.checkbox("Data Normalization"):
                    normalized = True
                    df = (df - df.min()) / (df.max() - df.min())
                else:
                    normalized = False

        # For grouped spectra sometimes we want to shift the spectra from each other, here it is:
        with main_expander:
            # TODO the code below needed?
            # trick to better fit sliders in expander
            # _, main_expander_column, _ = st.beta_columns([1, 38, 1])
            # with main_expander_column:

            shift_col, _, trim_col = st.beta_columns([5, 1, 5])
            with shift_col:
                if chart_type == 'GS':
                    shift = data_customisation.separate_spectra(normalized)
                elif chart_type == 'SINGLE':
                    col = st.selectbox('spectrum to plot', df.columns)
                    df = df[[col]]
                else:
                    shift = None
            with trim_col:
                df = vis_utils.trim_spectra(df)

        # data conversion end
        if spectra_conversion_type in {"OPT"}:
            baselines = pd.DataFrame(index=df.index)
            baselined = pd.DataFrame(index=df.index)
            flattened = pd.DataFrame(index=df.index)
            for col in df.columns:
                baselines[col] = peakutils.baseline(df[col], vals[col][0])
                baselined[col] = df[col] - baselines[col]
                flattened[col] = baselined[col].rolling(window=vals[col][1], min_periods=1, center=True).mean()

        #
        # # Plotting
        #

        # Groupped spectra
        if chart_type == 'GS':
            shifters = [(i + 1) * shift for i in range(len(df.columns))]
            plot_df = df if spectra_conversion_type == "RAW" else flattened
            plot_df = plot_df + shifters
    
            figs = [px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)]

        # Mean spectra
        elif chart_type == 'MS':
            if spectra_conversion_type == 'RAW':
                plot_df = df
                figs = [px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)]
    
            elif spectra_conversion_type in {'OPT'}:
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
            if spectra_conversion_type == "RAW":
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
            charts.show_charts(figs, plots_color, template)

        with col_left:
            st.markdown('')
            link = utils.download_button(plot_df.reset_index(), f'spectrum.csv',
                                         button_text='Download CSV')
            st.markdown(link, unsafe_allow_html=True)

    else:
        manual.show_manual()

    authors.show_developers()


if __name__ == '__main__':
    try:
        import streamlit_analytics
    
        credential_file = 'tmp_credentials.json'
        if not os.path.exists(credential_file):
            with open(credential_file, 'w') as infile:
                infile.write(st.secrets['firebase_credentials'])
            print('credentials written')
    
        collection = datetime.date.today().strftime("%Y-%m")
        with streamlit_analytics.track(firestore_key_file=credential_file,
                                       firestore_collection_name=collection,
                                       # verbose=True
                                       ):
            main()
    except KeyError:
        main()

    print("Streamlit finished it's work")
