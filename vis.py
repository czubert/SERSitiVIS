import pandas as pd
import streamlit as st

from processing import bwtek
from processing import renishaw
from processing import utils
from processing import wasatch
from processing import witec
from visualisation import custom_plot
from visualisation import draw

st.set_page_config(
    page_title="SERSitive.eu",
    page_icon="https://sersitive.eu/wp-content/uploads/cropped-icon.png",
    layout="wide",
    initial_sidebar_state="auto"
)

st.set_option('deprecation.showfileUploaderEncoding', False)

st.sidebar.image('examples/logo.png', use_column_width=True)

import os

conf_dir = os.path.expanduser('~') + '/.streamlit'
os.makedirs(conf_dir, exist_ok=True)
with open(conf_dir + '/config.toml', 'w') as infile:
    infile.write(
        """[theme]
primaryColor='#FF7733'
backgroundColor="#999999"
secondaryBackgroundColor="#F0F2F6"
textColor="#262730"
font="sans serif"
    """)
print("config file created")

SINGLE = 'Single spectra'
MS = 'Mean spectrum'
GS = 'Grouped spectra'
P3D = 'Plot 3D'
UplSpec = 'Upload "*.txt" spectra'
BWTEK = 'BWTEK'
RENI = 'Renishaw'
WITEC = 'WITec Alpha300 R+'
WASATCH = 'Wasatch System'
TELEDYNE = 'Teledyne Princeton Instruments'

TEST = 'Testing bwtek'

spectrometer = st.sidebar.radio(
    "",
    (BWTEK, RENI, WITEC, WASATCH, TELEDYNE), index=0)

files = st.sidebar.file_uploader(label='', accept_multiple_files=True, type=['txt', 'csv'])


separators = {'comma': ',', 'dot': '.', 'tab': '\t', 'space': ' '}

temp_data_df = None
temp_meta_df = None
df = None

if files:
    with st.beta_expander("Customize your chart"):
        plots_color = draw.choosing_colorway()
        template = draw.choose_template()

    if spectrometer == BWTEK:
        temp_data_df, temp_meta_df = bwtek.read_bwtek(files)
        df = utils.group_dfs(temp_data_df)
        custom_plot.bwtek_vis_options(df, plots_color, template)

    # Renishaw raw spectra
    elif spectrometer == RENI:

        reni_data = renishaw.read_renishaw(files, separators['space'])

        df = pd.concat([reni_data[data_df] for data_df in reni_data], axis=1)

        df.dropna(inplace=True, how='any', axis=0)

        display_opt = custom_plot.vis_options()
        custom_plot.show_plot(df, plots_color, template, display_opt=display_opt, key=None)

    # WITec raw spectra
    elif spectrometer == WITEC:
        witec_data = witec.read_witec(files, separators['comma'])

        df = pd.concat([witec_data[data_df] for data_df in witec_data], axis=1)

        display_opt = custom_plot.vis_options()
        custom_plot.show_plot(df, plots_color, template, display_opt=display_opt, key=None)

    elif spectrometer == WASATCH:
        # Read data and prepare it for plot
        data = wasatch.read_wasatch(files, separators['comma'])

        # Show possible options for visualisation - single/grouped spectra
        display_opt = custom_plot.vis_options()

        # Plot spectra
        custom_plot.show_plot(data, plots_color, template, display_opt=display_opt, key=None)

    # Renishaw raw spectra
    elif spectrometer == TELEDYNE:

        reni_data = renishaw.read_renishaw(files, separators['comma'])

        df = pd.concat([reni_data[data_df] for data_df in reni_data], axis=1)

        df.dropna(inplace=True, how='any', axis=0)

        display_opt = custom_plot.vis_options()
        custom_plot.show_plot(df, plots_color, template, display_opt=display_opt, key=None)

else:
    st.image('examples/logo.png', use_column_width=True)

    st.warning('First choose data type from left sidebar')
    st.warning('Then upload file or files for visualisation - left sidebar')
    st.header('Short manual on how to implement data')
    st.write('')

    with st.beta_expander('Download example date'):
        st.markdown("[Download data from OneDrive](https://1drv.ms/u/s!AlbmGPIOL6ElhvdePlcXvYwtt5YzbA?e=zsdF5j)")
        st.markdown("Password: sersitive")

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

    st.stop()

st.sidebar.markdown(f"\n\n\n")
st.sidebar.markdown(f"by")
st.sidebar.markdown(f"[Paweł Albrycht](https://www.linkedin.com/in/paweł-albrycht-b791147a/)")
st.sidebar.markdown(f"\n")
st.sidebar.markdown("")

print("Streamlit finish it's work")
