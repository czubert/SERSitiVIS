"""
Shared data: spectra are uploaded once in the sidebar and used on every page.
"""
import os

import pandas as pd
import streamlit as st

from core import readers

EXAMPLE_DIR = os.path.join('data', 'data_examples')
EXAMPLES = {
    'BWTEK': ['bwtek/bwtek(2).txt', 'bwtek/bwtek(3).txt'],
    'Renishaw': ['renishaw/renishaw(5).txt', 'renishaw/renishaw(6).txt'],
    'WITec Alpha300 R+': ['witec/WITec(5).csv', 'witec/WITec(7).csv'],
    'Wasatch': ['wasatch/SERSitive_next_day_1ppm-20201009-093810-270034-WP-00702.csv',
                'wasatch/SERSitive_next_day_2ppm-20201009-093705-137238-WP-00702.csv'],
    'Teledyne Princeton Instruments': ['teledyne/teledyne(1).csv', 'teledyne/teledyne(2).csv'],
    'Jobin Yvon T64000': ['jobin_yvon/4MPBA_9B22_10s_1x.txt', 'jobin_yvon/5MPBA_9B22_10s_1x.txt',
                          'jobin_yvon/6MPBA_9B22_10s_3x.txt'],
}
NO_EXAMPLE = '—'


def example_files(instrument):
    """:return: List of (name, bytes)"""
    files = []
    for path in EXAMPLES[instrument]:
        with open(os.path.join(EXAMPLE_DIR, path), 'rb') as f:
            files.append((os.path.basename(path), f.read()))
    return files


@st.cache_data(show_spinner='Reading files...')
def _read(files, file_format):
    return readers.read_files(files, file_format)


def data_sidebar():
    """
    Data loader shown in the sidebar on every page
    :return: DataFrame (index = Raman Shift, one column per spectrum) or None if no data
    """
    st.sidebar.subheader('Data')
    uploaded = st.sidebar.file_uploader('Upload spectra (*.txt, *.csv)',
                                        accept_multiple_files=True,
                                        type=['txt', 'csv'],
                                        key='workspace_files',
                                        help='Spectrometer type is detected automatically. '
                                             'You can upload files from different spectrometers at once.')
    if uploaded:
        files = [(f.name, f.getvalue()) for f in uploaded]
    else:
        example = st.sidebar.selectbox('...or try example data', [NO_EXAMPLE] + list(EXAMPLES),
                                       key='workspace_example')
        files = example_files(example) if example != NO_EXAMPLE else []

    with st.sidebar.expander('File format'):
        file_format = st.selectbox('File format', list(readers.FORMATS), format_func=readers.FORMATS.get,
                                   key='workspace_format',
                                   help='Change it only if a file is read incorrectly.')

    if not files:
        return None

    df, loaded, errors = _read(tuple(files), file_format)

    for name, error in errors.items():
        st.sidebar.error(f'**{name}**: {error}')

    if df is None:
        return None

    if df.empty:
        st.sidebar.error('Spectra do not share a common Raman Shift range - upload them separately.')
        return None

    with st.sidebar.expander(f'Loaded {df.shape[1]} spectra from {len(loaded)} files'):
        st.dataframe(pd.DataFrame([{'File': f.name,
                                    'Format': readers.FORMATS[f.format],
                                    'Spectra': f.data.shape[1]} for f in loaded]),
                     hide_index=True)
        st.caption(f'Raman Shift: {df.index.min():.0f} – {df.index.max():.0f} cm⁻¹, {len(df)} points')

    return df
