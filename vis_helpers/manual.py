
import re

import streamlit as st

from constants import LABELS
from processing import utils


def example_data_html(spectrometer):
    """
    Prepares string to show in manual, i.e. *.csv
    :param spectrometer: Str, name of the chosen spectrometer
    :return: Str
    """
    files = utils.load_example_files(spectrometer)
    text = files[0].read()
    files[0].seek(0)
    html = f'<div style="font-family: monospace"><p>{text}</p></div>'
    html = re.sub(r'\n', r'<br>', html)
    return html


def show_manual():
    """
    Shows manual on front page if data is not uploaded
    """
    
    # company logo
    # html_code = vis_utils.show_logo()
    # st.markdown(html_code, unsafe_allow_html=True)
    
    # warnings with tips how to work with this program
    st.header('Data visualisation')
    st.subheader('Short manual on how to import data')
    st.warning("First choose spectra type from left sidebar (if it doesn't work try different one)")
    st.warning('Then upload file or files for visualisation (or load example data) from left sidebar')
    st.write('')
    
    with st.expander('BWTEK'):
        st.write('Upload raw data in *.txt format')
        st.write('Original data consists of metadata and data')
        html = example_data_html('BWTEK')
        st.components.v1.html(html, height=200, scrolling=True)

    with st.expander('WITec Alpha300 R+'):
        st.write('Upload spectra in *.txt or *.csv format')
        st.write('First column is X axis i.e Raman Shift (name of column is not important)')
        st.write('Other columns should contain the intensity')
        st.markdown(f'<b>Name of column</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
        st.markdown(f"Do not duplicate names of the columns", unsafe_allow_html=True)
        html = example_data_html('WITEC')
        st.components.v1.html(html, height=200, scrolling=True)

    with st.expander('Renishaw'):
        st.write('Upload raw data in *.txt or *.csv format')
        st.write('First column is X axis i.e Raman Shift (name of column is not important)')
        st.write('Second column is Y axis, and should contain the intensity')
        st.markdown(f'<b>Name of a file</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
        html = example_data_html('RENI')
        st.components.v1.html(html, height=200, scrolling=True)

    with st.expander('Wasatch'):
        st.write('Upload raw data in *.txt or *.csv')
        html = example_data_html('WASATCH')
        st.components.v1.html(html, height=200, scrolling=True)

    with st.expander('Teledyne Princeton Instruments'):
        st.write('Upload raw data in *.txt or *.csv:')
        html = example_data_html('TELEDYNE')
        st.components.v1.html(html, height=200, scrolling=True)

    with st.expander(LABELS['JOBIN']):
        st.write('Upload raw data in *.txt or *.csv:')
        html = example_data_html('JOBIN')
        st.components.v1.html(html, height=200, scrolling=True)
