import streamlit as st
import numpy as np
import pandas as pd
import peakutils
import plotly.graph_objects as go

from . import draw
from processing import utils

SINGLE = 'Single spectra'
AV = 'Average'
BS = 'Baseline'
MS = 'Mean spectrum'
GS = 'Grouped spectra'
RS = 'Raman Shift'
DS = 'Dark Subtracted #1'
DEG = 'Polynominal degree'
WINDOW = 'Set window for spectra flattening'
DFS = {'ML model grouped spectra': 'Dark Subtracted #1', 'ML model mean spectra': 'Average'}
FLAT = 'Flattened'
COR = 'Corrected'
P3D = 'Plot 3D'
ORG = 'Original spectrum'


def show_plot(df, display_options_radio, key):
    """
    Based on uploaded files and denominator it shows either single plot of each spectra (file),
    all spectra on one plot or spectra of mean values
    :param df: DataFrame
    :param display_options_radio: String
    :param key: String
    :return:
    """
    st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

    plots_color = draw.choosing_colorway()

    template = draw.choose_template()

    if display_options_radio == SINGLE:
        df2 = df.copy()

        for col in range(len(df.columns)):
            st.write('========================================================================')
            deg = st.slider(f'{DEG} plot nr: {col}', min_value=1, max_value=20, value=5)
            window = st.slider(f'{WINDOW} plot nr: {col}', min_value=1, max_value=20, value=3)

            # Creating DataFrame that will be shown on plot
            df_to_show = pd.DataFrame(df2.iloc[:, col]).dropna()
            # Adding column with baseline that will be show on plot
            df_to_show[BS] = peakutils.baseline(df_to_show, deg)

            # Creating DataFrame with applied Baseline correction
            corrected_df = utils.correct_baseline_single(df_to_show, deg, df_to_show.columns[0])


            # Refining DataFrame to make spectra flattened
            corrected_df[FLAT] = corrected_df[COR].rolling(window=window).mean()
            corrected_df.dropna(inplace=True)

            # Showing spectra after baseline correction
            fig_single_corr = go.Figure()


            user_input_name = st.text_input("Type name of compound below", f'Spectra nr: {col}')

            fig_single_corr = draw.add_traces_single_spectra(corrected_df, fig_single_corr, x=RS, y=FLAT,
                                                             name=user_input_name)

            draw.fig_layout(template, fig_single_corr, plots_colorscale=plots_color,
                            descr=None)

            st.write(fig_single_corr)



            # Showing spectra before baseline correction + baseline function
            fig_single_all = go.Figure()
            if key == 'xy':
                DS = corrected_df.columns[0]
            else:
                DS = 'Dark Subtracted #1'
            fig_single_all = draw.add_traces(corrected_df, fig_single_all, x=RS, y=DS, name='Original spectra')
            fig_single_all = draw.add_traces(corrected_df, fig_single_all, x=RS, y=BS, name=BS)
            fig_single_all = draw.add_traces(corrected_df, fig_single_all, x=RS, y=COR, name=COR)
            fig_single_all = draw.add_traces(corrected_df, fig_single_all, x=RS, y=FLAT,
                                             name=f'{FLAT} + {BS} correction')
            draw.fig_layout(template, fig_single_all, plots_colorscale=plots_color,
                            descr=f'{ORG}, {BS}, and {FLAT} + {BS}')
            st.write(fig_single_all)


    elif display_options_radio == MS:
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

    elif display_options_radio == GS:
        st.write('========================================================================')
        user_input_name = st.text_input("Type name of compound below")

        # changing columns names, so they are separated on the plot,
        df2 = df.copy()
        df2.columns = np.arange(len(df2.columns))

        # Adding possibility to change degree of polynominal regression
        deg = st.slider(f'{DEG}', min_value=1, max_value=20, value=5)
        window = st.slider(f'{WINDOW}', min_value=1, max_value=20, value=3)

        # Baseline correction + drawing plot
        fig_grouped_corr = go.Figure()

        draw.fig_layout(template, fig_grouped_corr, plots_colorscale=plots_color,
                        descr=None)

        if key is None:
            for col in range(len(df2.columns)):
                corrected = pd.DataFrame(df2.iloc[:, col]).dropna()
                corrected = utils.correct_baseline(corrected, deg, window).dropna()
                fig_grouped_corr = draw.add_traces(corrected.reset_index(), fig_grouped_corr, x=RS, y=col,
                                                   name=f'{user_input_name} spectra nr: {col + 1}')

            st.write(fig_grouped_corr)

        elif key == 'xy':
            for col in range(len(df2.columns)):
                col_name = df.columns[col]
                corrected = pd.DataFrame(df.loc[:, col_name]).dropna()
                corrected = utils.correct_baseline(corrected, deg, window).dropna()
                fig_grouped_corr = draw.add_traces(corrected.reset_index(), fig_grouped_corr, x=RS, y=col_name,
                                                   name=f'{col_name} {user_input_name}')

            st.write(fig_grouped_corr)

        utils.show_dataframe(df2, key)

    elif display_options_radio == P3D:
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


def corrected_dfw_data_metadata(meta, data, no):
    """
    :param meta:
    :param data:
    :param no:
    :return:
    """
    important_idx = ['intigration times(ms)', 'laser_powerlevel', 'average number', 'time_multiply', 'yaxis_min',
                     'yaxis_max',
                     'xaxis_min', 'xaxis_max', 'interval_time', 'laser_wavelength', 'name']

    if st.button(f'Show data number: {no}'):
        st.dataframe(data[no])

    if st.button(f'Show metadata number: {no}'):
        st.dataframe(meta[no].loc[important_idx, :])
