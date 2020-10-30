import pandas as pd
import streamlit as st

from processing import utils
from visualisation import custom_plot
from visualisation import draw

st.write('lala ')
st.set_option('deprecation.showfileUploaderEncoding', False)
st.sidebar.image('examples/logo.png', use_column_width=True)

SINGLE = 'Single spectra'
MS = 'Mean spectrum'
GS = 'Grouped spectra'
P3D = 'Plot 3D'
UplSpec = 'Upload "*.txt" spectra'
BWTEK = 'BWTEK'
RENI = 'Renishaw'
witec = 'WITec Alpha300 R+'

spectrometer = st.sidebar.radio(
    "",
    (BWTEK, RENI, witec), index=0)

files = st.sidebar.file_uploader(label='', accept_multiple_files=True, type=['txt', 'csv'])

temp_data_df = None
temp_meta_df = None
df = None

if files:
    st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
    with st.beta_expander("Customize your chart"):
        plots_color = draw.choosing_colorway()
        template = draw.choose_template()

    # BWTEK raw spectra
    if spectrometer == BWTEK:
        temp_data_df, temp_meta_df = utils.read_data_metadata(files)
        df = utils.group_dfs(temp_data_df)
        custom_plot.bwtek_vis_options(df, plots_color, template)

    # Renishaw raw spectra
    elif spectrometer == RENI:
        separators = {'comma': ',', 'dot': '.', 'tab': '\t'}
        separator = st.sidebar.radio('Specify the separator', ('comma', 'dot', 'tab'), 2)

        reni_data = utils.read_data_metadata_renishaw(files, separators[separator])

        df = pd.concat([reni_data[data_df] for data_df in reni_data], axis=1)

        df.dropna(inplace=True, how='any', axis=0)

        display_opt = custom_plot.vis_options()
        custom_plot.show_plot(df, plots_color, template, display_opt=display_opt, key=None)

    # WITec raw spectra
    elif spectrometer == witec:
        separators = {'comma': ',', 'dot': '.', 'tab': '\t'}

        separator = st.sidebar.radio('Specify the separator', ('comma', 'dot', 'tab'))

        witec_data = utils.read_data_metadata_xy(files, separators[separator])

        df = pd.concat([witec_data[data_df] for data_df in witec_data], axis=1)

        display_opt = custom_plot.vis_options()
        custom_plot.show_plot(df, plots_color, template, display_opt=display_opt, key=None)

else:
    st.image('examples/logo.png', use_column_width=True)
    st.warning('Upload file or files for visualisation - left sidebar')
    st.header('Short manual on how to implement data')
    st.write('')
    with st.beta_expander('For BWTEK - upload raw data in *.txt format'):
        pass

    with st.beta_expander('For WITec Alpha300 R+, upload spectra in *.txt or *.csv format as follows:'):
        st.write(pd.read_csv('data_tests/witec/WITec(7).csv'))
        st.image('examples/witec.png', use_column_width=True)
        st.write('First column is X axis i.e Raman Shift (name of column is not important here)')
        st.write('Other columns should be the data itself')
        st.markdown(f'<b>Name of column</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)
        st.markdown(f"<p style='color:red'><b>Important:</b> Do not duplicate names of the columns",
                    unsafe_allow_html=True)

    with st.beta_expander('For Renishaw spectra upload raw data in *.txt or *.csv format as shown below:'):
        st.write(pd.read_csv('data_tests/renishaw/renishaw(6).txt', header=None, sep='\t'))
        st.image('examples/reni.png', use_column_width=True)
        st.write('First column is X axis i.e Raman Shift (name of column is not important here)')
        st.write('Second column is Y axis, and should be the data itself')
        st.markdown(f'<b>Name of a file</b> will be displayed as a <b>name of a plot in the legend</b>',
                    unsafe_allow_html=True)

    st.stop()

print("Streamlit finish it's work")
