import html

import streamlit as st

from core import readers
from vis_helpers import workspace

FORMAT_NOTES = {
    'BWTEK': ['Upload raw data in *.txt format (metadata + data).'],
    'Renishaw': ['First column: Raman Shift, second column: intensity.',
                 'Name of the file is used as the name of the spectrum.'],
    'WITec Alpha300 R+': ['First column: Raman Shift, other columns: intensities.',
                          'Column names are shown in the legend. A file may contain several Raman Shift columns.'],
    'Wasatch': ['Upload *.csv (ENLIGHTEN export) or *.txt files.'],
    'Teledyne Princeton Instruments': ['First column: Raman Shift, second column: intensity.'],
    'Jobin Yvon T64000': ['First column: Raman Shift, second column: intensity.'],
}


def example_data_html(instrument):
    """
    Beginning of an example file, to show in the manual
    :param instrument: Str, key of workspace.EXAMPLES
    :return: Str
    """
    name, raw = workspace.example_files(instrument)[0]
    text = html.escape(readers.decode(raw))
    return f'<div style="font-family: monospace; white-space: pre">{text}</div>'


def show_manual():
    """
    Shows manual on front page if data is not uploaded
    """
    st.header('Data visualisation')
    st.subheader('How to start')
    st.info('Upload your spectra (*.txt or *.csv) in the left sidebar, or choose example data. '
            'Spectrometer type is detected automatically - you can upload files from different instruments at once.')
    st.write('')

    st.subheader('Supported files')
    for instrument, notes in FORMAT_NOTES.items():
        with st.expander(instrument):
            for note in notes:
                st.write(note)
            st.components.v1.html(example_data_html(instrument), height=200, scrolling=True)
