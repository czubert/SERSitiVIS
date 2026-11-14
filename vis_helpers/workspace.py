"""
Shared data: spectra are uploaded once in the sidebar and used on every page.

Loaded files are kept in plain session_state keys (not only in widget state), because Streamlit may reset
widgets when switching pages - the data must survive that.
"""
import os

import pandas as pd
import streamlit as st

from core import readers
from vis_helpers.i18n import t, choice

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
DEFAULT_EXAMPLE = 'Jobin Yvon T64000'  # p-MBA, three spectra
NO_EXAMPLE = '—'
FILE_TYPES = ['txt', 'csv', 'wdf', 'spc', 'jdx', 'dx', 'jcamp']

# session_state keys
FILES = '_ws_files'  # list of (name, bytes)
EXAMPLE = '_ws_example'
FORMAT = '_ws_format'
UPLOADER_VERSION = '_ws_uploader_version'  # changing it gives a fresh, empty uploader

EXAMPLE_WIDGET = 'workspace_example'
FORMAT_WIDGET = 'workspace_format'


def example_files(instrument):
    """:return: List of (name, bytes)"""
    files = []
    for path in EXAMPLES[instrument]:
        with open(os.path.join(EXAMPLE_DIR, path), 'rb') as f:
            files.append((os.path.basename(path), f.read()))
    return files


def load_example(instrument):
    """Loads example data. Can be used in a widget callback (e.g. a button on the start page)."""
    st.session_state[EXAMPLE] = instrument
    st.session_state[EXAMPLE_WIDGET] = instrument
    st.session_state[FILES] = example_files(instrument) if instrument != NO_EXAMPLE else []


def clear():
    st.session_state[FILES] = []
    st.session_state[EXAMPLE] = NO_EXAMPLE
    st.session_state[EXAMPLE_WIDGET] = NO_EXAMPLE
    st.session_state[UPLOADER_VERSION] = st.session_state.get(UPLOADER_VERSION, 0) + 1


def _uploader_key():
    return f'workspace_files_{st.session_state.get(UPLOADER_VERSION, 0)}'


def _on_upload():
    uploaded = st.session_state[_uploader_key()]
    st.session_state[FILES] = [(f.name, f.getvalue()) for f in uploaded]
    st.session_state[EXAMPLE] = NO_EXAMPLE
    st.session_state[EXAMPLE_WIDGET] = NO_EXAMPLE


def _on_example():
    load_example(st.session_state[EXAMPLE_WIDGET])


@st.cache_data(show_spinner=False)
def _read(files, file_format):
    return readers.read_files(files, file_format)


def data_sidebar():
    """
    Data loader shown in the sidebar on every page
    :return: DataFrame (index = Raman Shift, one column per spectrum) or None if no data
    """
    st.session_state.setdefault(FILES, [])
    st.session_state.setdefault(EXAMPLE, NO_EXAMPLE)
    st.session_state.setdefault(FORMAT, 'AUTO')
    # restore widgets from the stored values (widget state may be gone after a page change)
    st.session_state.setdefault(EXAMPLE_WIDGET, st.session_state[EXAMPLE])

    st.sidebar.subheader(t('Data'))
    st.sidebar.file_uploader(t('Upload spectra'),
                             accept_multiple_files=True,
                             type=FILE_TYPES,
                             key=_uploader_key(),
                             on_change=_on_upload,
                             help=t('Spectrometer type is detected automatically. You can upload files from '
                                    'different spectrometers at once. Formats: *.txt, *.csv, Renishaw *.wdf, '
                                    'Galactic *.spc, JCAMP-DX *.jdx.'))

    st.sidebar.selectbox(t('...or try example data'), [NO_EXAMPLE] + list(EXAMPLES),
                         key=EXAMPLE_WIDGET, on_change=_on_example)

    with st.sidebar.expander(t('File format')):
        st.session_state[FORMAT] = choice('selectbox', t('File format'), list(readers.FORMATS), key=FORMAT_WIDGET,
                                          format_func=lambda f: t(readers.FORMATS[f]),
                                          help=t('Change it only if a file is read incorrectly.'))

    files = st.session_state[FILES]
    if not files:
        return None

    with st.spinner(t('Reading files...')):
        df, loaded, errors = _read(tuple(files), st.session_state[FORMAT])

    for name, error in errors.items():
        st.sidebar.error(f'**{name}**: {t(error)}')

    if df is not None and df.empty:
        st.sidebar.error(t('Spectra do not share a common Raman Shift range - upload them separately.'))
        df = None

    saturated = [name for f in loaded for name in f.saturated]
    if saturated:
        st.sidebar.warning(t('Detector saturated in: {names}. The top of the strongest peak is cut off, so its '
                             'height is too low (e.g. EF lower by ~10 %). Measure again with lower laser power or a '
                             'shorter time.').format(names=', '.join(map(str, saturated))),
                           icon=':material/warning:')

    if loaded:
        with st.sidebar.expander(t('Loaded {spectra} spectra from {files} files').format(
                spectra=0 if df is None else df.shape[1], files=len(loaded))):
            st.dataframe(pd.DataFrame([{t('File'): f.name,
                                        t('Format'): t(readers.FORMATS[f.format]),
                                        t('Spectra'): f.data.shape[1]} for f in loaded]),
                         hide_index=True)
            if df is not None:
                st.caption(t('Raman Shift: {low} – {high} cm⁻¹, {points} points').format(
                    low=f'{df.index.min():.0f}', high=f'{df.index.max():.0f}', points=len(df)))

    st.sidebar.button(t('Clear data'), on_click=clear, icon=':material/delete:')
    return df


def stored_uploader(label, key):
    """
    File uploader whose files survive page changes (stored in session_state).
    :return: (list of (name, bytes), DataFrame or None) - files and spectra read from them
    """
    store, version = f'_stored_{key}', f'_stored_{key}_version'
    st.session_state.setdefault(store, [])
    widget_key = f'{key}_{st.session_state.get(version, 0)}'

    def on_change():
        st.session_state[store] = [(f.name, f.getvalue()) for f in st.session_state[widget_key] or []]

    def on_clear():
        st.session_state[store] = []
        st.session_state[version] = st.session_state.get(version, 0) + 1

    st.file_uploader(label, accept_multiple_files=True, type=FILE_TYPES, key=widget_key, on_change=on_change)

    files = st.session_state[store]
    if not files:
        return files, None

    df, loaded, errors = _read(tuple(files), st.session_state.get(FORMAT, 'AUTO'))
    for name, error in errors.items():
        st.error(f'**{name}**: {t(error)}')

    # after a page change the uploader is empty again, but the files are still loaded
    if not st.session_state.get(widget_key):
        st.caption(', '.join(name for name, _ in files))
    st.button(t('Clear data'), key=f'{key}_clear', on_click=on_clear, icon=':material/delete:')
    return files, df


def file_names():
    """Names of the files loaded in the sidebar (for reports)"""
    return [name for name, _ in st.session_state.get(FILES, [])]
