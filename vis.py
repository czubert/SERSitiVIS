import pandas as pd
import peakutils
import plotly.express as px
import streamlit as st

from constants import LABELS
from for_streamlit_only import manual, sidebar, data_customisation, charts, authors
from processing import save_read
from processing import utils
from visualisation import draw
from visualisation import visualisation_options as vis_opt


def main():
    """
    Main is responsible for the visualisation of everything connected with streamlit.
    It is the web application itself.
    """
    
    # Sets header, logo and radiobuttons in a row
    sidebar.sidebar_head()
    
    #
    # # Spectrometer type - BWTek / Renishaw / Witec / Wasatch / Teledyne
    #
    st.sidebar.write('#### Choose spectra type', unsafe_allow_html=True)
    spectrometer = st.sidebar.selectbox(
        "",
        (LABELS['BWTEK'], LABELS['RENI'], LABELS['WITEC'], LABELS['WASATCH'], LABELS['TELEDYNE']),
        index=0)
    
    # User data loader
    st.sidebar.write('#### Upload your data or try with ours', unsafe_allow_html=True)
    files = st.sidebar.file_uploader(label='', accept_multiple_files=True, type=['txt', 'csv'])
    
    # Allow example data loading when no custom data are loaded
    if not files:
        # st.sidebar.write('#### Or try with our', unsafe_allow_html=True)
        if st.sidebar.checkbox("Load example data"):
            files = utils.load_example_files(spectrometer)
    
    # Check if data loaded, if yes, perform actions
    if files:
        df = save_read.read_files(spectrometer, files)

        main_expander = st.beta_expander("Customize your chart")
        # Choose plot colors and templates
        with main_expander:
            plots_color, template = draw.choosing_colorway(), draw.choose_template()

        # Select chart type
        chart_type = vis_opt.vis_options(spectrometer)
        
        # Select data conversion type
        spectra_conversion_type = vis_opt.convertion_opt()
        
        # TODO need improvements
        # getting rid of duplicated columns
        df = df.loc[:, ~df.columns.duplicated()]
        
        #
        # # data manipulation - raw / optimization / normalization
        #
        
        # Normalization
        if spectra_conversion_type == LABELS["NORM"]:
            df = (df - df.min()) / (df.max() - df.min())
        
        # Mean Spectra
        if chart_type == LABELS['MS']:
            df = df.mean(axis=1).rename('Average').to_frame()

        with main_expander:
            # trick to better fit sliders in expander
            _, main_expander_column, _ = st.beta_columns([1, 38, 1])
            with main_expander_column:
    
                # For grouped spectra sometimes we want to shift the spectra from each other, here it is:
                if chart_type == LABELS['GS']:
                    shift = data_customisation.get_shifting_distance(spectra_conversion_type)
                else:
                    shift = None
        
        # Every chart (or pair) gets its own columns
        tmp_cols = [st.beta_columns([5, 2]) for _ in df.columns]
        cols_left, cols_right = zip(*tmp_cols)
        df, vals = data_customisation.get_deg_win(df, chart_type, spectra_conversion_type, cols_right, df.columns)
        
        # data conversion end
        if spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]}:
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
        if chart_type == LABELS['GS']:
            shifters = [(i + 1) * shift for i in range(len(df.columns))]
            plot_df = df if spectra_conversion_type == LABELS["RAW"] else flattened
            plot_df = plot_df + shifters
            
            figs = [px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)]
        
        # Mean spectra
        elif chart_type == LABELS['MS']:
            if spectra_conversion_type == LABELS["RAW"]:
                plot_df = df
                figs = [px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)]

            elif spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]}:
                columns = ['Average', 'Baseline', 'BL-Corrected', 'Flattened + BL-Corrected']
                plot_df = pd.concat([df, baselines, baselined, flattened], axis=1)
                plot_df.columns = columns

                fig1 = px.line(plot_df, x=plot_df.index, y=columns[-1], color_discrete_sequence=plots_color[3:])
                fig2 = px.line(plot_df, x=plot_df.index, y=plot_df.columns, color_discrete_sequence=plots_color)
                figs = [(fig1, fig2)]
            else:
                raise ValueError('Unknown conversion type for Mean spectrum chart')
        # 3D spectra
        elif chart_type == LABELS['P3D']:
            plot_df = flattened if spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]} else df

            plot_df = plot_df.reset_index().melt('Raman Shift', plot_df.columns)
            fig = px.line_3d(plot_df, x='variable', y='Raman Shift', z='value', color='variable')

            camera = dict(eye=dict(x=1.9, y=0.15, z=0.2))
            fig.update_layout(scene_camera=camera,
                              width=1200, height=1200,
                              margin=dict(l=1, r=1, t=30, b=1),
                              )
            figs = [fig]
        
        # Single spectra
        elif chart_type == LABELS['SINGLE']:
            if spectra_conversion_type == LABELS["RAW"]:
                plot_df = df
                figs = [px.line(plot_df[col], color_discrete_sequence=plots_color) for col in plot_df.columns]
            else:
                columns = ['Average', 'Baseline', 'BL-Corrected', 'Flattened + BL-Corrected']
                figs = []
                plot_dfs = []
                for col_left, col in zip(cols_left, df.columns):
                    plot_df = pd.concat([df[col], baselines[col], baselined[col], flattened[col]], axis=1)
                    plot_df.columns = columns

                    fig1 = px.line(plot_df, x=plot_df.index, y=columns[-1],
                                   color_discrete_sequence=plots_color[3:])  # trick for color consistency
                    fig2 = px.line(plot_df, x=plot_df.index, y=plot_df.columns,
                                   color_discrete_sequence=plots_color)
                    fig_tup = (fig1, fig2)
                    figs.append(fig_tup)
                    plot_dfs.append(plot_df)
        else:
            raise ValueError("Something unbelievable has been chosen")

        charts.show_charts(cols_left, figs, plots_color, template)

        # TODO this is just until we change SINGLE plots to one plot per site.
        #  than we'll resign of the loop
        if chart_type == LABELS['SINGLE'] and spectra_conversion_type != LABELS["RAW"]:
            for col_left, plot_df in zip(cols_left, plot_dfs):
                with col_left:
                    link = utils.download_button(plot_df.reset_index(), f'spectrum.csv',
                                                 button_text='Download plot as CSV file')
                    st.markdown(link, unsafe_allow_html=True)
        else:
            link = utils.download_button(plot_df.reset_index(), f'spectrum.csv',
                                         button_text='Download CSV')
            st.markdown(link, unsafe_allow_html=True)

    else:
        manual.show_manual()
    
    authors.show_developers()


if __name__ == '__main__':
    main()
    print("Streamlit finished it's work")
