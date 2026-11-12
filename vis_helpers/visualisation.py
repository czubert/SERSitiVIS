import pandas as pd
import plotly.express as px
import streamlit as st

from core import processing
from vis_helpers import manual, data_customisation, charts, vis_utils
from vis_helpers.vis_utils import print_widgets_separator
from visualisation import visualisation_options as vis_opt


def visualisation(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    if df is None:
        manual.show_manual()
        return

    print_widgets_separator(1, sidebar=True)

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

    # Mean Spectra
    if chart_type == 'MS':
        df = df.mean(axis=1).rename('Average').to_frame()

    # columns in main view. Chart, expanders
    # TODO rozwiązać to jakoś sprytniej

    col_left, col_right = st.columns([5, 2])

    if chart_type == 'SINGLE':
        with col_left:
            col = st.selectbox('Spectrum', df.columns)
            df = df[[col]]

    with col_right:
        normalized = False

        # # Plot settings
        plot_settings = st.expander("Plot settings", expanded=False)

        # # Choose plot colors and templates
        with plot_settings:
            plots_color, template = vis_utils.get_chart_vis_properties_vis()
            chart_titles = vis_utils.get_plot_description()

        # # Range and separation
        range_expander_name = 'Range' if chart_type in {'SINGLE', 'MS'} else 'Range and separation'
        range_expander = st.expander(range_expander_name, expanded=False)

        with range_expander:
            df = vis_utils.trim_spectra(df)

        if spectra_conversion_type != "RAW":

            # # Data Manipulation
            with st.expander("Data Manipulation", expanded=False):
                vals = data_customisation.get_deg_win(chart_type, spectra_conversion_type, df.columns)

                normalized = st.checkbox("Normalize")
                if normalized:
                    df = (df - df.min()) / (df.max() - df.min())

    # data conversion end
    if spectra_conversion_type == 'OPT':
        baselines, baselined, flattened = processing.baseline_and_smooth(df, vals)

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
        st.download_button('Download CSV',
                           data=plot_df.reset_index().to_csv(index=False),
                           file_name='spectrum.csv',
                           mime='text/csv')

