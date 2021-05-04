import base64
import re

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from constants import LABELS
from processing import bwtek
from processing import renishaw
from processing import utils
from processing import wasatch
from processing import witec
from visualisation import draw
from visualisation import grouped_spectra
from visualisation import mean_spectra
from visualisation import p3d_spectra
from visualisation import single_spectra
from visualisation import visualisation_options as vis_opt


def example_data_html(spectrometer):
    files = utils.load_example_files(LABELS[spectrometer])
    text = files[0].read()
    files[0].seek(0)
    html = f'<div style="font-family: monospace"><p>{text}</p></div>'
    html = re.sub(r'\n', r'<br>', html)
    return html


st.set_page_config(
    page_title="SERSitive.eu",
    page_icon="https://sersitive.eu/wp-content/uploads/cropped-icon.png",
    layout="wide",
    initial_sidebar_state="auto"
)

# radiobuttons in one row
st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
st.set_option('deprecation.showfileUploaderEncoding', False)

# linked logo of sersitive at the sidebar
link = 'http://sersitive.eu'

with open('examples/sersitivis_no_background.png', 'rb') as f:
    data = f.read()
bin_str = base64.b64encode(data).decode()

html_code = f'''
    <a href="{link}">
        <img src="data:image/png;base64,{bin_str}"
        style="padding:0px 6px 5px 0px; 20px; height:80px"/>
    </a>'''

st.sidebar.markdown(html_code, unsafe_allow_html=True)
st.sidebar.markdown('')
st.sidebar.markdown('')

st.sidebar.write('#### Choose spectra type', unsafe_allow_html=True)
spectrometer = st.sidebar.radio(
    "",
    (LABELS['BWTEK'], LABELS['RENI'], LABELS['WITEC'], LABELS['WASATCH'], LABELS['TELEDYNE']), index=0)

# users data lodaer
st.sidebar.write('#### Upload your data', unsafe_allow_html=True)
files = st.sidebar.file_uploader(label='', accept_multiple_files=True, type=['txt', 'csv'])

# allow example data loading when no custom data are loaded
if not files:
    st.sidebar.write('#### Or try with our', unsafe_allow_html=True)
    if st.sidebar.checkbox("Load example data"):
        files = utils.load_example_files(spectrometer)

df = None

if files:
    # BWTek raw spectra
    if spectrometer == LABELS['BWTEK']:
        df, bwtek_metadata = bwtek.read_bwtek(files)

    # Renishaw raw spectra
    elif spectrometer == LABELS['RENI']:
        df = renishaw.read_renishaw(files, " ")

    # WITec raw spectra
    elif spectrometer == LABELS['WITEC']:
        df = witec.read_witec(files, ',')

    # WASATCH raw spectra
    elif spectrometer == LABELS['WASATCH']:
        df = wasatch.read_wasatch(files, ',')

    # Teledyne raw spectra
    elif spectrometer == LABELS['TELEDYNE']:
        df = renishaw.read_renishaw(files, ',')

    # choose plot colors and tamplates
    with st.beta_expander("Customize your chart"):
        plots_color, template = draw.choosing_colorway(), draw.choose_template()

    # lets you select chart type
    chart_type = vis_opt.vis_options(spectrometer)

    # lets you select data conversion type
    spectra_conversion_type = vis_opt.convertion_opt()

    # TODO need improvements
    # getting rid of duplicated columns
    df = df.loc[:, ~df.columns.duplicated()]

    # All possible types of charts
    data_vis_option = {LABELS['SINGLE']: single_spectra.show_single_plots,
                       LABELS['MS']: mean_spectra.show_mean_plot,
                       LABELS['GS']: grouped_spectra.show_grouped_plot,
                       LABELS['P3D']: p3d_spectra.show_3d_plots}

    # # Run specified type of chart with chosen parameters
    # For grouped spectra sometimes we want to shift the spectra from each other, here it is:
    if chart_type == LABELS['GS']:
        # depending on conversion type we have to adjust the scale
        if spectra_conversion_type == LABELS['NORM']:
            shift = st.slider(LABELS['SHIFT'], 0.0, 1.0, 0.0, 0.1)
        else:
            shift = st.slider(LABELS['SHIFT'], 0, 30000, 0, 250)

        data_vis_option[chart_type](df, plots_color, template, spectra_conversion_type, shift)
    # All the other conversion types are single therefore no need for shift spectra
    else:
        data_vis_option[chart_type](df, plots_color, template, spectra_conversion_type)


else:
    st.markdown(f'''
        <img src="https://sersitive.eu/wp-content/uploads/LOGO.png"
        style="
        margin: auto;
        width: 80%;
        padding:0px 6px 45px 25%; 20px;
        "/>''',
                unsafe_allow_html=True
                )

    st.warning('First choose data type')
    st.warning('Then upload single or multiple files for visualisation')
    st.header('Short manual on how to prepare files')
    st.write('')

    # TODO needs improvements, shows data only if BWTEK is choosen
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

    import authors

    authors.contact_developers()

    authors.made_by()
    authors.made_by_pawel()
    authors.made_by_lukasz()

    st.stop()

import authors

authors.made_by()
authors.made_by_pawel()
authors.made_by_lukasz()

print("Streamlit finish it's work")

