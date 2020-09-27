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
    plots_color = draw.plot_color()
    template = draw.choose_template()

    if display_options_radio == SINGLE:

        for col in range(len(df.columns)):
            df2 = df.copy()

            deg = st.slider(f'{DEG} plot nr: {col}', min_value=1, max_value=20, value=5)
            window = st.slider(f'{WINDOW} plot nr: {col}', min_value=1, max_value=20, value=3)


            # # Peakutils data preparation
            # corrected_df = df2.reset_index()
            # indexes = peakutils.indexes(corrected_df[DS], thres=0.1, min_dist=35)
            # interpolate = peakutils.interpolate(corrected_df[RS].values, corrected_df[DS].values, ind=indexes)
            # st.write('interpolate')
            # st.write(interpolate)

            # Creating DataFrame that will be shown on plot
            df_to_show = pd.DataFrame(df2.iloc[:, col]).dropna()

            # Adding column with baseline that will be show on plot
            df_to_show[BS] = peakutils.baseline(df_to_show, deg)

            # Creating DataFrame with applied Baseline correction
            corrected_df = utils.correct_baseline_single(df_to_show, deg)

            # Refining DataFrame to make spectra flattened
            corrected_df[FLAT] = corrected_df['Corrected'].rolling(window=window).mean()
            corrected_df.dropna(inplace=True)

            # Showing spectra after baseline correction
            fig2 = draw.draw_plot(corrected_df, x=RS, y=FLAT, plot_color=plots_color, color=None)
            fig2 = draw.fig_layout(template, fig2, 'Spectra after baseline correction')
            st.write(fig2)


            # Showing spectra before baseline correction + baseline function
            fig = draw.draw_plot(corrected_df, x=RS, y=DS, plot_color=plots_color, color=None)
            fig = draw.add_traces(corrected_df, fig, x=RS, y=DS, name='Original spectra', col=col)
            fig = draw.add_traces(corrected_df, fig, x=RS, y=BS, name=BS, col=col)
            fig = draw.add_traces(corrected_df, fig, x=RS, y=FLAT, name=f'{FLAT} + {BS} correction', col=col)
            fig = draw.fig_layout(template, fig, 'Original spectra + baseline')
            st.write(fig)

    elif display_options_radio == MS:
        # getting mean values for each raman shift
        df2 = df.copy()
        df2[DS] = df2.mean(axis=1)
        df2 = df2.loc[:, [DS]]

        # getting baseline for mean spectra
        deg = st.slider(f'{DEG}', min_value=1, max_value=20, value=5)
        window = st.slider(f'{WINDOW}', min_value=1, max_value=20, value=3)

        # Preparing data to plot
        df2[BS] = peakutils.baseline(df2.loc[:, DS], deg)
        df2 = utils.correct_baseline_single(df2, deg)
        df2[FLAT] = df2['Corrected'].rolling(window=window).mean()
        df2.dropna(inplace=True)

        # Drowing figure of mean spectra after baseline correction and flattening
        fig2 = draw.draw_plot(utils.correct_baseline(df2, deg), x=df2.reset_index()[RS], y=FLAT, plot_color=plots_color, color=None)
        fig2 = draw.fig_layout(template, fig2, 'Mean spectra after baseline correction')
        st.write(fig2)

        # Drowing figure of mean spectra  + baseline
        fig = draw.draw_plot(df2, x=df2.reset_index()[RS], y=DS, plot_color=plots_color, color=None)
        fig.add_traces([go.Scatter(x=df2.reset_index()[RS], y=df2[DS], name=MS)])
        fig.add_traces([go.Scatter(x=df2.reset_index()[RS], y=df2[COR], name=COR)])
        fig.add_traces([go.Scatter(x=df2.reset_index()[RS], y=df2[FLAT], name=FLAT)])
        fig.add_traces([go.Scatter(x=df2.reset_index()[RS], y=df2[BS], name=BS)])
        draw.fig_layout(template, fig, 'Original spectra, baseline, corrected, and corrected + flattened')
        st.write(fig)

    elif display_options_radio == GS:
        # changing columns names, so they are separated on the plot,
        df.columns = np.arange(len(df.columns))

        # Adding possibility to change degree of polynominal regression
        deg = st.slider(f'{DEG}', min_value=1, max_value=20, value=5)

        # Baseline correction
        df2 = df.copy()
        st.write(df2)
        df2 = utils.correct_baseline(df2, deg)
        df2 = df2.reset_index()

        # Showing spectra after baseline correction
        corrected_df = pd.melt(df2, id_vars=df2.columns[0], value_vars=df2.columns[1:])
        fig = draw.draw_plot(corrected_df, x=RS, y='value', plot_color=plots_color, color='variable')
        fig = draw.fig_layout(template, fig, GS)
        st.write(fig)

        utils.show_dataframe(df, key)


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
