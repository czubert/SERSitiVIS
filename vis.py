import streamlit as st

from visualisation import custom_plot
from processing import utils

st.sidebar.title('Menu')

SINGLE = 'Single spectra'
MS = 'Mean spectrum'
GS = 'Grouped spectra'
USpec = 'Upload "*.txt" spectra'
BWTEK = 'BWTEK'
RENI = 'Renishaw'

files = st.sidebar.file_uploader(USpec, type=['txt', 'csv'])

spectrometer = st.sidebar.radio(
    "Choose from which spectrometer did you upload spectra",
    (BWTEK, RENI), index=0)

temp_data_df = None
temp_meta_df = None
df = None


def vis_options(df):
    # showing sidebar
    display_options_radio = st.sidebar.radio(
        "What would you like to see?",
        (SINGLE, MS, GS), index=0)

    if display_options_radio == SINGLE:
        st.title(SINGLE)
        custom_plot.show_plot(df, display_options_radio=SINGLE, key=None)

    elif display_options_radio == MS:
        st.title(f'{MS} of multiple spectra')
        custom_plot.show_plot(df, display_options_radio=MS, key=None)

    elif display_options_radio == GS:
        st.title(f'{GS} on one plot')
        custom_plot.show_plot(df, display_options_radio=GS, key=None)

    print("Streamlit finish it's work")



if files is not None:
    if spectrometer == BWTEK:
        temp_data_df, temp_meta_df = utils.read_data_metadata(files)
        df = utils.group_dfs(temp_data_df)
        vis_options(df)

    elif spectrometer == RENI:
        st.write('Under construction - showing results for BWTEK')
        temp_data_df, temp_meta_df = utils.read_data_metadata(files)
        df = utils.group_dfs(temp_data_df)
        vis_options(df)
else:
    st.write('Upload data for visualisation.')
