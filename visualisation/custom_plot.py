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
DFS = {'ML model grouped spectra': 'Dark Subtracted #1', 'ML model mean spectra': 'Average'}


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
            df2[BS] = peakutils.baseline(df2.iloc[:, col], deg)

            fig2 = draw.draw_plot(utils.correct_baseline(df2.iloc[:, [col]], deg), x=None, y=DS, plot_color=plots_color,
                                  color=None)
            fig2 = draw.fig_layout(template, fig2, 'Spectra after baseline correction')
            st.write(fig2)

            fig = draw.draw_plot(df2.iloc[:, [col]], x=None, y=DS, plot_color=plots_color, color=None)
            fig.add_traces([go.Scatter(y=df2.iloc[:, [col]][DS], name=MS)])
            fig.add_traces([go.Scatter(y=df2.iloc[:, [-1]][BS], name=BS)])
            fig = draw.fig_layout(template, fig, 'Original spectra + baseline')
            st.write(fig)

    elif display_options_radio == MS:
        # getting mean values for each raman shift
        df2 = df.copy()
        df2[AV] = df2.mean(axis=1)
        # df2.reset_index(inplace=True)
        df2 = df2.loc[:, [AV]]

        # getting baseline for mean spectra
        deg = st.slider(f'{DEG}', min_value=1, max_value=20, value=5)

        df2['base_line'] = peakutils.baseline(df2.loc[:, AV], deg)

        fig2 = draw.draw_plot(utils.correct_baseline(df2, deg), x=None, y=AV, plot_color=plots_color, color=None)
        fig2 = draw.fig_layout(template, fig2, 'Spectra after baseline correction')
        st.write(fig2)

        fig = draw.draw_plot(df2,  x=None, y=AV, plot_color=plots_color, color=None)
        fig.add_traces([go.Scatter(y=df2[AV], name=MS)])
        fig.add_traces([go.Scatter(y=df2['base_line'], name=BS)])
        draw.fig_layout(template, fig, 'Original spectra + baseline')
        st.write(fig)

    elif display_options_radio == GS:
        # changing columns names, so they are separated on the plot,
        # before all columns had the same name
        df.columns = np.arange(len(df.columns))

        deg = st.slider(f'{DEG}', min_value=1, max_value=20, value=5)

        # drawing the plot
        df2 = df.copy()

        df2 = utils.correct_baseline(df2, deg)
        df2 = df2.reset_index()

        corrected_df = pd.melt(df2, id_vars=df2.columns[0], value_vars=df2.columns[1:])

        fig = draw.draw_plot(corrected_df, x=RS, y='value', plot_color=plots_color, color='variable')

        fig = draw.fig_layout(template, fig, GS)

        st.write(fig)

        utils.show_dataframe(df, key)


def show_data_metadata(meta, data, no):
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
