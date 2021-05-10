import base64
import io

import pandas as pd
import peakutils
import plotly.express as px
import streamlit as st

import authors
from constants import LABELS
from processing import bwtek
from processing import utils
from processing.save_read import read_files
from visualisation import draw
from visualisation import visualisation_options as vis_opt


def main():
    sidebar_head()

    st.sidebar.write('#### Choose spectra type', unsafe_allow_html=True)
    spectrometer = st.sidebar.radio(
        "",
        (LABELS['BWTEK'], LABELS['RENI'], LABELS['WITEC'], LABELS['WASATCH'], LABELS['TELEDYNE']), index=0)

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

        # # Run specified type of chart with chosen parameters
        # For grouped spectra sometimes we want to shift the spectra from each other, here it is:
        col1, col2 = st.beta_columns([5, 2])

        #
        # # data manipulation - raw / optimization / normalization
        #
        if spectra_conversion_type == LABELS["NORM"]:
            df = (df - df.min()) / (df.max() - df.min())

        if chart_type == LABELS['MS']:
            df = df.mean(axis=1).rename('Average').to_frame()
        elif chart_type == LABELS['GS']:
            # depending on conversion type we have to adjust the scale
            if spectra_conversion_type == LABELS['NORM']:
                shift = st.slider(LABELS['SHIFT'], 0.0, 1.0, 0.0, 0.1)
            else:
                shift = st.slider(LABELS['SHIFT'], 0, 30000, 0, 250)

        if spectra_conversion_type == LABELS['RAW']:
            vals = None
        elif chart_type == LABELS['MS']:
            with col2:
                deg = utils.choosing_regression_degree()
                window = utils.choosing_smoothening_window()
                vals = {col: (deg, window) for col in df.columns}
        elif chart_type == LABELS['SINGLE']:
            tmp_cols = [st.beta_columns([5,2]) for col in df.columns]
            cols1, cols2 = zip(*tmp_cols)
            vals = {}

            for col2, col in zip(cols2, df.columns):
                with col2:
                    st.write(col)
                    vals[col] = (utils.choosing_regression_degree(None, col), utils.choosing_smoothening_window(None, col))
        else:
            adjust_plots_globally = st.radio(
                "Adjust all spectra or each spectrum?",
                ('all', 'each'), index=0)

            with col2:
                with st.beta_expander("Customize spectra", expanded=True):
                    if adjust_plots_globally == 'all':
                        deg = utils.choosing_regression_degree()
                        window = utils.choosing_smoothening_window()
                        vals = {col: (deg, window) for col in df.columns}
                    else:
                        vals = {}
                        for col in df.columns:
                            st.write(col)
                            vals[col] = (utils.choosing_regression_degree(None, col),
                                         utils.choosing_smoothening_window(None, col))

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
            if spectra_conversion_type == LABELS["RAW"]:
                shifters = [(i + 1) * shift for i in range(len(df.columns))]
                df = df + shifters

                fig = px.line(df, x=df.index, y=df.columns, color_discrete_sequence=plots_color)

            else:
                shifters = [(i + 1) * shift for i in range(len(df.columns))]
                flattened = flattened + shifters

                fig = px.line(flattened, x=flattened.index, y=flattened.columns, color_discrete_sequence=plots_color)

        elif chart_type == LABELS['MS']:
            if spectra_conversion_type == LABELS["RAW"]:
                fig = px.line(df, x=df.index, y=df.columns, color_discrete_sequence=plots_color)
            elif spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]}:
                columns = ['Average', 'Baseline', 'BL-Corrected', 'Flattened + BL-Corrected']
                plot_df = pd.concat([df, baselines, baselined, flattened], axis=1)
                plot_df.columns = columns

                fig1 = px.line(plot_df, x=plot_df.index, y=columns[-1], color_discrete_sequence=plots_color[3:])
                fig2 = px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)
                fig = [fig1, fig2]
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

        elif chart_type == LABELS['SINGLE']:

            if spectra_conversion_type == LABELS["RAW"]:
                fig = [px.line(df[col], color_discrete_sequence=plots_color) for col in df.columns]
            else:
                columns = ['Average', 'Baseline', 'BL-Corrected', 'Flattened + BL-Corrected']
                for col1, col in zip(cols1, df.columns):
                    plot_df = pd.concat([df[col], baselines[col], baselined[col], flattened[col]], axis=1)
                    plot_df.columns = columns

                    fig1 = px.line(plot_df, x=plot_df.index, y=columns[-1], color_discrete_sequence=plots_color[3:])
                    draw.fig_layout(template, fig1, plots_colorscale=plots_color)
                    fig1.update_traces(line=dict(width=3.5))

                    fig2 = px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)
                    draw.fig_layout(template, fig2, plots_colorscale=plots_color)
                    fig2.update_traces(line=dict(width=3.5))

                    with col1:
                        st.plotly_chart(fig1, use_container_width=True)
                        with st.beta_expander('Detailed view'):
                            st.plotly_chart(fig2, use_container_width=True)
                fig = []
        else:
            raise ValueError("Something unbelievable has been chosen")

        with col1:
            if isinstance(fig, (list, tuple)):
                for f in fig:
                    draw.fig_layout(template, f, plots_colorscale=plots_color)
                    f.update_traces(line=dict(width=3.5))
                    st.plotly_chart(f, use_container_width=True)
            else:
                draw.fig_layout(template, fig, plots_colorscale=plots_color)
                fig.update_traces(line=dict(width=3.5))
                st.plotly_chart(fig, use_container_width=True)

    else:
        show_manual()

    authors.show_developers()


def show_manual():
    st.markdown(f'''
            <img src="https://sersitive.eu/wp-content/uploads/LOGO.png"
            style="
            margin: auto;
            width: 80%;
            padding:0px 6px 45px 25%; 20px;
            "/>''',
                unsafe_allow_html=True
                )
    st.warning('First choose data type from left sidebar')
    st.warning('Then upload file or files for visualisation - sidebar')
    st.header('Short manual on how to import data')
    st.write('')
    # TODO needs improvements, shows data only if BWTEK is choosen
    with st.beta_expander('For BWTEK - upload raw data in *.txt format without any changes'):
        streams = utils.load_example_files('BWTEK')
        df, bwtek_metadata = bwtek.read_bwtek(streams[0:1])
        st.markdown('### Original data consists of metadata')
        st.write(bwtek_metadata)
        st.markdown('### And data')
        st.write(df)
    with st.beta_expander('For WITec Alpha300 R+, upload spectra in *.txt or *.csv format as follows:'):
        st.write(pd.read_csv('data_examples/witec/WITec(7).csv'))
        st.write('First column is X axis i.e Raman Shift (name of column is not important here)')
        st.write('Other columns should be the data itself')
        st.markdown(f'<b>Name of column</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
        st.markdown(f"<p style='color:red'><b>Important:</b> Do not duplicate names of the columns",
                    unsafe_allow_html=True)
    with st.beta_expander('For Renishaw spectra upload raw data in *.txt or *.csv format as shown below:'):
        st.write(pd.read_csv('data_examples/renishaw/renishaw(6).txt', header=None, sep='\t'))
        st.write('First column is X axis i.e Raman Shift (name of column is not important here)')
        st.write('Second column is Y axis, and should be the data itself')
        st.markdown(f'<b>Name of a file</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
    with st.beta_expander('For Wasatch spectra upload raw data in *.txt or *.csv:'):
        st.write(pd.read_csv('data_examples/wasatch/SERSitive_next_day_1ppm-20201009-093810-270034-WP-00702.csv',
                             header=None, sep='\t'))
    with st.beta_expander('For Teledyne Princeton Instruments spectra upload raw data in *.txt or *.csv:'):
        st.write(pd.read_csv('data_examples/teledyne/teledyne(1).csv',
                             header=None, sep=','))


def sidebar_head():
    st.set_page_config(
        page_title="SERSitive.eu",
        page_icon="https://sersitive.eu/wp-content/uploads/cropped-icon.png",
        layout="wide",
        initial_sidebar_state="auto"
    )

    # radiobuttons in one row
    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
    st.set_option('deprecation.showfileUploaderEncoding', False)
    # linked logo of sersitive at the sidebar
    link = 'http://sersitive.eu'

    with open('examples/sersitivis_no_background.png', 'rb') as f:
        data = f.read()

    bin_str = base64.b64encode(data).decode()
    html_code = f'''
        <a href="{link}">
            <img src="data:image/png;base64,{bin_str}"
            style="padding:0px 6px 5px 0px; 20px; height:80px"/>
        </a>'''

    st.sidebar.markdown(html_code, unsafe_allow_html=True)
    st.sidebar.markdown('')
    st.sidebar.markdown('')


if __name__ == '__main__':
    main()
    print("Streamlit finished it's work")
