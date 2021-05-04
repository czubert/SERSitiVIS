import base64

import pandas as pd
import streamlit as st

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

        grouped_spectra.show_grouped_plot(df, plots_color, template, spectra_conversion_type, shift)



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

    st.warning('First choose data type from left sidebar')
    st.warning('Then upload file or files for visualisation - sidebar')
    st.header('Short manual on how to import data')
    st.write('')

    # TODO needs improvements, shows data only if BWTEK is choosen
    with st.beta_expander('For BWTEK - upload raw data in *.txt format without any changes'):
        if spectrometer == LABELS['BWTEK']:
            files = utils.load_example_files(spectrometer)
            df, bwtek_metadata = bwtek.read_bwtek(files)
            st.markdown('### Original data consists of metadata')
            st.write(bwtek_metadata)
            st.markdown('### And data')
            st.write(df)

    with st.beta_expander('For WITec Alpha300 R+, upload spectra in *.txt or *.csv format as follows:'):
        st.write(pd.read_csv('data_examples/witec/WITec(7).csv'))
        st.write('First column is X axis i.e Raman Shift (name of column is not important here)')
        st.write('Other columns should be the data itself')
        st.markdown(f'<b>Name of column</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
        st.markdown(f"<p style='color:red'><b>Important:</b> Do not duplicate names of the columns",
                    unsafe_allow_html=True)

    with st.beta_expander('For Renishaw spectra upload raw data in *.txt or *.csv format as shown below:'):
        st.write(pd.read_csv('data_examples/renishaw/renishaw(6).txt', header=None, sep='\t'))
        st.write('First column is X axis i.e Raman Shift (name of column is not important here)')
        st.write('Second column is Y axis, and should be the data itself')
        st.markdown(f'<b>Name of a file</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)

    with st.beta_expander('For Wasatch spectra upload raw data in *.txt or *.csv:'):
        st.write(pd.read_csv('data_examples/wasatch/SERSitive_next_day_1ppm-20201009-093810-270034-WP-00702.csv',
                             header=None, sep='\t'))

    with st.beta_expander('For Teledyne Princeton Instruments spectra upload raw data in *.txt or *.csv:'):
        st.write(pd.read_csv('data_examples/teledyne/teledyne(1).csv',
                             header=None, sep=','))

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
