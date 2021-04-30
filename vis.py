import base64

import pandas as pd
import streamlit as st

from processing import bwtek
from processing import renishaw
from processing import utils
from processing import wasatch
from processing import witec
from visualisation import draw
from visualisation import grouped_spectra as gs
from visualisation import mean_spectra as ms
from visualisation import p3d_spectra as p3d
from visualisation import single_spectra as ss
from visualisation import visualisation_options as vo

SINGLE = 'Single spectra'
MS = "Mean spectrum"
GS = "Grouped spectra"
P3D = "Plot 3D"


UplSpec = 'Upload "*.txt" spectra'
BWTEK = 'BWTEK'
RENI = 'Renishaw'
WITEC = 'WITec Alpha300 R+'
WASATCH = 'Wasatch System'
TELEDYNE = 'Teledyne Princeton Instruments'
SEPARATORS = {'comma': ',', 'dot': '.', 'tab': '\t', 'space': ' '}

TEST = 'Testing bwtek'

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
    (BWTEK, RENI, WITEC, WASATCH, TELEDYNE), index=0)

# users data lodaer
st.sidebar.write('#### Upload your data', unsafe_allow_html=True)
files = st.sidebar.file_uploader(label='', accept_multiple_files=True, type=['txt', 'csv'])

# allow example data loading when no custom data are loaded
if not files:
    st.sidebar.write('#### Or try with our', unsafe_allow_html=True)
    if st.sidebar.checkbox("Load example data"):
        files = utils.load_example_files(spectrometer)

temp_data_df = None
temp_meta_df = None
df = None

if files:
    # BWTek raw spectra
    if spectrometer == BWTEK:
        temp_data_df, temp_meta_df = bwtek.read_bwtek(files)
        df = pd.concat([data_df for data_df in temp_data_df.values()], axis=1)
        df.dropna(axis=1, inplace=True, how='all')

    # Renishaw raw spectra
    elif spectrometer == RENI:
        reni_data = renishaw.read_renishaw(files, SEPARATORS['space'])
        df = pd.concat([reni_data[data_df] for data_df in reni_data], axis=1)
        df.dropna(inplace=True, how='any', axis=0)

    # WITec raw spectra
    elif spectrometer == WITEC:
        witec_data = witec.read_witec(files, SEPARATORS['comma'])
        df = pd.concat([witec_data[data_df] for data_df in witec_data], axis=1)
        # st.write(df)

    # WASATCH raw spectra
    elif spectrometer == WASATCH:
        # Read data and prepare it for plot
        df = wasatch.read_wasatch(files, SEPARATORS['comma'])

    # Teledyne raw spectra
    elif spectrometer == TELEDYNE:
        reni_data = renishaw.read_renishaw(files, SEPARATORS['comma'])
        df = pd.concat([reni_data[data_df] for data_df in reni_data], axis=1)
        df.dropna(inplace=True, how='any', axis=0)
        st.write(df)

    # choose plot colors and tamplates
    plots_color, template = draw.adjust_plot_colors_n_templates()

    # lets you select chart type
    chart_type = vo.vis_options(spectrometer)

    # lets you select data conversion type
    spectra_conversion_type = vo.convertion_opt()

    # All possible types of charts
    data_vis_option = {SINGLE: ss.show_single_plots,
                       MS: ms.show_mean_plot,
                       GS: gs.show_grouped_plot,
                       P3D: p3d.show_3d_plots}

    # run specified type of chart with chosen parameters
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

    st.warning('First choose data type from left sidebar')
    st.warning('Then upload file or files for visualisation - sidebar')
    st.header('Short manual on how to import data')
    st.write('')

    with st.beta_expander('For BWTEK - upload raw data in *.txt format'):
        st.write('Update raw data from BWTek without any changes')

    with st.beta_expander('For WITec Alpha300 R+, upload spectra in *.txt or *.csv format as follows:'):
        st.write(pd.read_csv('data_examples/witec/WITec(7).csv'))
        st.image('examples/witec.png', use_column_width=True)
        st.write('First column is X axis i.e Raman Shift (name of column is not important here)')
        st.write('Other columns should be the data itself')
        st.markdown(f'<b>Name of column</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
        st.markdown(f"<p style='color:red'><b>Important:</b> Do not duplicate names of the columns",
                    unsafe_allow_html=True)

    with st.beta_expander('For Renishaw spectra upload raw data in *.txt or *.csv format as shown below:'):
        st.write(pd.read_csv('data_examples/renishaw/renishaw(6).txt', header=None, sep='\t'))
        st.image('examples/reni.png', use_column_width=True)
        st.write('First column is X axis i.e Raman Shift (name of column is not important here)')
        st.write('Second column is Y axis, and should be the data itself')
        st.markdown(f'<b>Name of a file</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)

    with st.beta_expander('For Wasatch spectra upload raw data in *.txt or *.csv:'):
        st.write('*.csv data obtains metadata, therefore one can add important matadata to the plot name')
        st.image('examples/wasatch_wo_name.png', use_column_width=True)
        st.image('examples/wasatch_with_name.png', use_column_width=True)

    import authors

    authors.made_by()
    authors.made_by_pawel()
    authors.made_by_lukasz()

    st.stop()

import authors

authors.made_by()
authors.made_by_pawel()
authors.made_by_lukasz()

print("Streamlit finish it's work")
