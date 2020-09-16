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

files = st.sidebar.file_uploader(USpec)

spectrometer = st.sidebar.radio(
    "Choose from which spectrometer did you upload spectra",
    (BWTEK, RENI), index=0)

temp_data_df = None
temp_meta_df = None
df = None


def vis_options(df, template='plotly'):
    # showing sidebar
    display_options_radio = st.sidebar.radio(
        "What would you like to see?",
        (SINGLE, MS, GS), index=0)

    if display_options_radio == SINGLE:
        st.title(SINGLE)
        custom_plot.show_plot(template, df, SINGLE, key=None)

    elif display_options_radio == MS:
        st.title(f'{MS} of multiple spectra')
        custom_plot.show_plot(template, df, MS, key=None)

    elif display_options_radio == GS:
        st.title(f'{GS} on one plot')
        custom_plot.show_plot(template, df, GS, key=None)

    print("Streamlit finish it's work")


def templates():
    chart_template = st.sidebar.radio(
        "Choose chart template",
        ('ggplot2', 'seaborn', 'simple_white', 'plotly',
         'plotly_white', 'plotly_dark', 'presentation', 'xgridoff',
         'ygridoff', 'gridon', 'none'), index=1)

    return chart_template


if files is not None:
    if spectrometer == BWTEK:
        temp_data_df, temp_meta_df = utils.read_data_metadata(files)
        df = utils.group_dfs(temp_data_df)
        template = templates()
        vis_options(df, template)

    elif spectrometer == RENI:
        st.write('Under construction - showing results for BWTEK')
        temp_data_df, temp_meta_df = utils.read_data_metadata(files)
        df = utils.group_dfs(temp_data_df)
        template = templates()
        vis_options(df, template)
else:
    st.write('Upload data for visualisation.')
