import pandas as pd
import peakutils
import plotly.graph_objects as go
import streamlit as st

from processing import utils
from . import draw

SINGLE = 'Single spectra'
AV = 'Average'
BS = 'Baseline'
MS = 'Mean spectrum'
GS = 'Grouped spectra'
RS = 'Raman Shift'
DS = 'Dark Subtracted #1'
DEG = 'Polynominal degree'
WINDOW = 'Set window for spectra flattening'
DFS = {'ML model grouped spectra': f'{DS}', 'ML model mean spectra': f'{AV}'}
FLAT = 'Flattened'
COR = 'Corrected'
P3D = 'Plot 3D'
ORG = 'Original spectrum'
RAW = "Raw Data"
OPT = "Optimised Data"
OPT_S = "Optimised Spectrum"


def show_plot(df, plots_color, template, display_opt, key):
    """
    Based on uploaded files and denominator it shows either single plot of each spectra (file),
    all spectra on one plot or spectra of mean values
    :param df: DataFrame
    :param display_opt: String
    :param key: String
    :return:
    """
    if display_opt == SINGLE:
        df2 = df.copy()

        for col in range(len(df.columns)):
            st.write('========================================================================')

            # Creating DataFrame that will be shown on plot
            df_to_show = pd.DataFrame(df2.iloc[:, col]).dropna()

            # TODO What might be useful - would be a function to choose which part of the spectrum should be
            # TODO used for the baseline fitting.
            # Adding column with baseline that will be show on plot

            # Showing spectra after baseline correction
            fig_single_corr = go.Figure()

            raw_spectra = st.radio(
                "What you would like to see?",
                (RAW, OPT), key='raw'
            )

            if raw_spectra == RAW:
                df_visual = df_to_show
                plot_line = df_visual.columns[0]
                description = ORG
            else:
                plot_line = FLAT
                description = OPT_S
                col1, col2 = st.beta_columns(2)
                with col1:
                    deg = st.slider(f'{DEG} plot nr: {col}', min_value=0, max_value=20, value=5, key=f'{col}')
                with col2:
                    window = st.slider(f'{WINDOW} plot nr: {col}', min_value=1, max_value=20, value=3, key=f'{col}')

                df_to_show[BS] = peakutils.baseline(df_to_show[df_to_show.columns[0]], deg)

                # Creating DataFrame with applied Baseline correction
                corrected_df = utils.correct_baseline_single(df_to_show, deg, df_to_show.columns[0])
                # Refining DataFrame to make spectra flattened
                corrected_df[FLAT] = corrected_df[COR].rolling(window=window).mean()
                corrected_df.dropna(inplace=True)

                df_visual = corrected_df

                # Showing spectra before baseline correction + baseline function
                fig_single_all = go.Figure()
                draw.fig_layout(template, fig_single_all, plots_colorscale=plots_color,
                                descr=f'{ORG}, {BS}, and {FLAT} + {BS}')

                specs = {'org': df_visual.columns[0], BS: BS, COR: COR, FLAT: FLAT}

                for spec in specs.keys():
                    if spec == FLAT:
                        name = f'{FLAT} + {BS} correction'
                    else:
                        name = specs[spec]

                    fig_single_all = draw.add_traces(df_visual, fig_single_all,
                                                     x=RS, y=specs[spec], name=name)

            fig_single_corr = draw.add_traces_single_spectra(df_visual, fig_single_corr, x=RS, y=plot_line,
                                                             name=df_visual.columns[0])

            draw.fig_layout(template, fig_single_corr, plots_colorscale=plots_color, descr=description)

            if raw_spectra == RAW:
                st.write(fig_single_corr)
            else:
                st.write(fig_single_corr)
                st.write(fig_single_all)



    elif display_opt == MS:
        # getting mean values for each raman shift
        df2 = df.copy()
        df2[AV] = df2.mean(axis=1)
        df2 = df2.loc[:, [AV]]

        # getting baseline for mean spectra
        deg = st.slider(f'{DEG}', min_value=1, max_value=20, value=5)
        window = st.slider(f'{WINDOW}', min_value=1, max_value=20, value=3)

        # Preparing data to plot
        df2[BS] = peakutils.baseline(df2.loc[:, AV], deg)
        df2 = utils.correct_baseline_single(df2, deg, MS)
        df2[FLAT] = df2['Corrected'].rolling(window=window).mean()
        df2.dropna(inplace=True)

        # Drowing figure of mean spectra after baseline correction and flattening
        fig_mean_corr = go.Figure()
        fig_mean_corr = draw.add_traces_single_spectra(df2, fig_mean_corr, x=RS, y=FLAT,
                                                       name=f'{FLAT} + {BS} correction')
        fig_mean_corr = draw.fig_layout(template, fig_mean_corr, plots_colorscale=plots_color,
                                        descr='Mean spectra after baseline correction')
        st.write(fig_mean_corr)

        # Drowing figure of mean spectra  + baseline
        fig_mean_all = go.Figure()
        fig_mean_all = draw.add_traces(df2, fig_mean_all, x=RS, y=AV, name=AV)
        fig_mean_all = draw.add_traces(df2, fig_mean_all, x=RS, y=BS, name=BS)
        fig_mean_all = draw.add_traces(df2, fig_mean_all, x=RS, y=COR, name=COR)
        fig_mean_all = draw.add_traces(df2, fig_mean_all, x=RS, y=FLAT, name=f'{FLAT} + {BS} correction')
        draw.fig_layout(template, fig_mean_all, plots_colorscale=plots_color,
                        descr=f'{ORG}, {BS}, {COR}, and {COR}+ {FLAT}')
        st.write(fig_mean_all)

    elif display_opt == GS:
        st.write('========================================================================')

        fig_grouped_corr = go.Figure()
        draw.fig_layout(template, fig_grouped_corr, plots_colorscale=plots_color,
                        descr=None)

        with st.beta_expander("Adjust your plots"):

            shift = st.slider('Shift spectra from each other', 0, 30000, 0, 250)

            for col in range(len(df.columns)):
                col1, col2 = st.beta_columns(2)
                with col1:
                    deg = st.slider(f'{DEG} for: {df.columns[col]}', min_value=1, max_value=20, value=5, key=f'{col}')
                with col2:
                    window = st.slider(f'{WINDOW} for: {df.columns[col]}', min_value=1, max_value=20, value=3,
                                       key=f'{col}')

                col_name = df.columns[col]

                corrected = pd.DataFrame(df.loc[:, col_name]).dropna()

                corrected = utils.correct_baseline(corrected, deg, window).dropna()

                if col != 0:
                    corrected.iloc[:, 0] += shift * col

                fig_grouped_corr = draw.add_traces(corrected.reset_index(), fig_grouped_corr, x=RS, y=col_name,
                                                   name=f'{df.columns[col]}')

        st.write(fig_grouped_corr)

    elif display_opt == P3D:
        df2 = df.copy()
        df2.columns = ['widmo nr ' + str(i) for i in range(len(df2.columns))]
        import plotly.express as px
        # Adding possibility to change degree of polynominal regression
        deg = st.slider(f'{DEG}', min_value=1, max_value=20, value=5)
        window = st.slider(f'{WINDOW}', min_value=1, max_value=20, value=3)

        # Baseline correction + flattening
        df2 = utils.correct_baseline(df=df2, deg=deg, window=window)
        # drawing a plot
        df2 = df2.reset_index()
        df2m = df2.melt('Raman Shift', df2.columns[1:])
        df2m_drop = df2m.dropna()

        fig_3d = px.line_3d(df2m_drop, x='variable', y=RS, z='value', color='variable')

        draw.fig_layout(template, fig_3d, plots_colorscale=plots_color,
                        descr=f'{P3D} with {COR} + {FLAT} spectra')

        camera = dict(
            eye=dict(x=1.9, y=0.15, z=0.2)
        )

        fig_3d.update_layout(scene_camera=camera,
                             width=900,
                             height=900,
                             margin=dict(l=1, r=1, t=30, b=1),
                             )

        st.write(fig_3d)


def bwtek_vis_options(df, plots_color, template):
    # showing sidebar
    display_options_radio = st.sidebar.radio(
        "What would you like to see?",
        (SINGLE, MS, GS, P3D), index=0)
    if display_options_radio == SINGLE:
        st.title(SINGLE)
        show_plot(df, plots_color, template, display_opt=SINGLE, key=None)

    elif display_options_radio == MS:
        st.title(f'{MS} of multiple spectra')
        st.subheader('Do not take mean spectra of different compounds')
        show_plot(df, plots_color, template, display_opt=MS, key=None)

    elif display_options_radio == GS:
        st.title(f'{GS} on one plot')
        show_plot(df, plots_color, template, display_opt=GS, key=None)

    elif display_options_radio == P3D:
        st.title(f'{P3D} on one plot')
        show_plot(df, plots_color, template, display_opt=P3D, key=None)


def vis_options():
    display_opt = SINGLE
    chart_type = st.sidebar.radio('Choose type of chart', (SINGLE, GS), 0)

    if chart_type == SINGLE:
        display_opt = SINGLE
    elif chart_type == GS:
        display_opt = GS

    return display_opt
