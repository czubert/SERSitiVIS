import base64
import re

import streamlit as st

from constants import LABELS
from processing import utils


def example_data_html(spectrometer):
    """
    Shows example data as a raw file, i.e. *.csv
    :param spectrometer: Str, name of the chosen spectrometer
    :return: Str
    """
    files = utils.load_example_files(LABELS[spectrometer])
    text = files[0].read()
    files[0].seek(0)
    html = f'<div style="font-family: monospace"><p>{text}</p></div>'
    html = re.sub(r'\n', r'<br>', html)
    return html


def show_manual():
    """
    Shows manual on front page if data is not uploaded
    """
    
    with open('logos/logo.png', 'rb') as f:
        data = f.read()
    
    bin_str = base64.b64encode(data).decode()
    html_code = f'''
                    <img src="data:image/png;base64,{bin_str}"
                    style="
                         margin: auto;
                         margin-top:-30px;
                         width: 65%;
                         padding:0px 6px 20px 25%;
                         "/>
                '''
    
    st.markdown(html_code, unsafe_allow_html=True)
    
    st.warning('First choose data type from left sidebar')
    st.warning('Then upload file or files for visualisation - sidebar')
    st.header('Short manual on how to import data')
    st.write('')
    
    with st.beta_expander('BWTEK'):
        st.write('Upload raw data in *.txt format')
        st.write('Original data consists of metadata and data')
        html = example_data_html('BWTEK')
        st.components.v1.html(html, height=200, scrolling=True)
    
    with st.beta_expander('WITec Alpha300 R+'):
        st.write('Upload spectra in *.txt or *.csv format')
        st.write('First column is X axis i.e Raman Shift (name of column is not important)')
        st.write('Other columns should contain the intensity')
        st.markdown(f'<b>Name of column</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
        st.markdown(f"Do not duplicate names of the columns", unsafe_allow_html=True)
        html = example_data_html('WITEC')
        st.components.v1.html(html, height=200, scrolling=True)
    
    with st.beta_expander('Renishaw'):
        st.write('Upload raw data in *.txt or *.csv format')
        st.write('First column is X axis i.e Raman Shift (name of column is not important)')
        st.write('Second column is Y axis, and should contain the intensity')
        st.markdown(f'<b>Name of a file</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
        html = example_data_html('RENI')
        st.components.v1.html(html, height=200, scrolling=True)
    
    with st.beta_expander('Wasatch'):
        st.write('Upload raw data in *.txt or *.csv')
        html = example_data_html('WASATCH')
        st.components.v1.html(html, height=200, scrolling=True)
    
    with st.beta_expander('Teledyne Princeton Instruments'):
        st.write('Upload raw data in *.txt or *.csv:')
        html = example_data_html('TELEDYNE')
        st.components.v1.html(html, height=200, scrolling=True)
