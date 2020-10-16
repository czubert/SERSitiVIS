import streamlit as st
import pandas as pd
import numpy as np

from visualisation import custom_plot
from processing import utils

st.set_option('deprecation.showfileUploaderEncoding', False)

st.sidebar.title('Menu')

SINGLE = 'Single spectra'
MS = 'Mean spectrum'
GS = 'Grouped spectra'
P3D = 'Plot 3D'
USpec = 'Upload "*.txt" spectra'
BWTEK = 'BWTEK'
RENI = 'Renishaw'
xy = 'WITec Alpha300 R+'

spectrometer = st.sidebar.radio(
    "First choose type of uploaded spectra",
    (BWTEK, RENI, xy), index=0)

files = st.sidebar.file_uploader(USpec, type=['txt', 'csv'])

temp_data_df = None
temp_meta_df = None
df = None


def vis_options(df):
    # showing sidebar
    display_options_radio = st.sidebar.radio(
        "What would you like to see?",
        (SINGLE, MS, GS, P3D), index=0)

    if display_options_radio == SINGLE:
        st.title(SINGLE)
        custom_plot.show_plot(df, display_options_radio=SINGLE, key=None)

    elif display_options_radio == MS:
        st.title(f'{MS} of multiple spectra')
        st.subheader('Do not take mean spectra of different compounds')
        custom_plot.show_plot(df, display_options_radio=MS, key=None)

    elif display_options_radio == GS:
        st.title(f'{GS} on one plot')
        custom_plot.show_plot(df, display_options_radio=GS, key=None)

    elif display_options_radio == P3D:
        st.title(f'{P3D} on one plot')
        custom_plot.show_plot(df, display_options_radio=P3D, key=None)

    print("Streamlit finish it's work")


if files is not None:
    if spectrometer == BWTEK:
        temp_data_df, temp_meta_df = utils.read_data_metadata(files)
        df = utils.group_dfs(temp_data_df)
        vis_options(df)

    elif spectrometer == RENI:
        separators = {'comma': ',', 'dot': '.', 'tab': '\t'}
        separator = st.sidebar.radio('Specify the separator', ('comma', 'dot', 'tab'), 2)
        chart_type = st.sidebar.radio('Choose type of chart', (SINGLE, GS))

        xy_data = utils.read_data_metadata_renishaw(files, separators[separator])

        df = pd.concat([data_df for data_df in xy_data], axis=1)
        df.dropna(inplace=True, how='any', axis=0)

        if chart_type == SINGLE:
            custom_plot.show_plot(df, display_options_radio=SINGLE, key=None)
        elif chart_type == GS:
            custom_plot.show_plot(df, display_options_radio=GS, key=None)

    elif spectrometer == xy:
        separators = {'comma':',', 'dot':'.','tab':'\t'}

        separator = st.sidebar.radio('Specify the separator', ('comma', 'dot', 'tab'))
        chart_type = st.sidebar.radio('Choose type of chart', (SINGLE, GS))

        xy_data = utils.read_data_metadata_xy(files, separators[separator])

        if chart_type == SINGLE:
            for df in xy_data:
                custom_plot.show_plot(df, display_options_radio=SINGLE, key='xy')
        elif chart_type == GS:
            for df in xy_data:
                custom_plot.show_plot(df, display_options_radio=GS, key='xy')



else:
    st.subheader('Upload data for visualisation.')
    st.write('* For BWTEK: upload raw data in *.txt format')

    st.write('* For WITec Alpha300 R+ spectra upload *.txt or *.csv file as follows:')
    if st.button('WITec example'):
        st.write(pd.read_csv('data_tests/witec/WITec(7).csv'))
        st.write('"Unnamed" (this column in data should not be named) is column of Raman Shift,')
        st.write('uM/nM/pM are Intenities')

    if st.button('WITec second example'):
        st.write(pd.read_csv('data_tests/witec/WITec(5).csv'))
        st.write('"Unnamed" (this column in data should not be named) are columns of Raman Shift,')
        st.write('mM/uM are Intenities - name it according to the data provided')

    st.write('* For Renishaw spectra upload raw data in *.txt or *.csv format as shown below:')
    if st.button('Renishaw example'):
        st.write(pd.read_csv('data_tests/renishaw/renishaw(6).txt'))
        st.write('Data should be x + y where x is Raman Shift and y is intensity. Do not provide column names')
