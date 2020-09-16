import streamlit as st
import numpy as np
import peakutils

from . import draw
from processing import utils

SINGLE = 'Single spectra'
MS = 'Mean spectrum'
GS = 'Grouped spectra'
RS = 'Raman Shift'
DEG = 'Polynominal degree'
DFS = {'ML model grouped spectra': 'Dark Subtracted #1', 'ML model mean spectra': 'Average'}


def show_plot(df, display_options_radio, key):
    """
    Based on uploaded files and denominator it shows either single plot of each spectra (file),
    all spectra on one plot or spectra of mean values
    :param uploaded_files: File
    :param denominator: Int
    :param display_options_radio: String
    :param key: String
    :return:
    """

    template = None

    if display_options_radio == SINGLE:
        for col in range(len(df.columns)):
            df3 = df.copy()
            df3.reset_index(inplace=True)

            deg = st.slider(f'{DEG} plot nr: {col}', min_value=1, max_value=20, value=5)

            # df3['Baseline'] = peakutils.baseline(df3['Dark Subtracted #1'], deg)

            # TODO dokonczycz update tego figa
            # fig = draw.draw_plot(df3.iloc[:, [0, col + 1, col + 2]], y_value=GS)

            # st.write(draw.draw_plot(df3.iloc[:, [0, col + 1]], y_value='Custom'))
            #
            # if st.button(f'Correct baseline, plot nr: {col}'):
            #     df2 = utils.correct_baseline(df.copy(), deg)
            #     df2.reset_index(inplace=True)
            #
            #     st.write(draw.draw_plot(df2.iloc[:, [0, col + 1]], y_value='Custom'))

            df2 = utils.correct_baseline(df.copy(), deg)
            df2.reset_index(inplace=True)

            st.write(draw.draw_plot(template, df2.iloc[:, [0, col + 1]], y_value='Custom'))


    elif display_options_radio == MS:
        df['Average'] = df.mean(axis=1)
        df2 = df.copy()
        df2.reset_index(inplace=True)
        st.write(draw.draw_plot(template, df2, y_value=MS))
        utils.show_dataframe(df2, key)

    elif display_options_radio == GS:
        # changing columns names, so they are separated on the plot,
        # before all columns had the same name
        df.columns = np.arange(len(df.columns))
        # drawing the plot
        st.write(draw.draw_plot(template, df, y_value=GS))
        utils.show_dataframe(df, key)


    chart_template = st.radio(
        "Choose from which spectrometer did you upload spectra",
        ('ggplot2', 'seaborn', 'simple_white', 'plotly',
         'plotly_white', 'plotly_dark', 'presentation', 'xgridoff',
         'ygridoff', 'gridon', 'none'), index=0)

    templates = ['ggplot2', 'seaborn', 'simple_white', 'plotly',
         'plotly_white', 'plotly_dark', 'presentation', 'xgridoff',
         'ygridoff', 'gridon', 'none']

    for templ in templates:
        if chart_template == templ:
            template = templ

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
