import base64
import io
import json
import os.path
import pickle
import re
import uuid

import pandas as pd
import peakutils
import streamlit as st
from bs4 import UnicodeDammit

from constants import LABELS


def read_spec(uploaded_file, spectra_params, meta_params=None):
    """
    Reads csv file and returns it, if metadata available returns also metadata
    :param uploaded_file: csv file
    :param spectra_params: Dict
    :param meta_params: Dict
    :return: DataFrame
    """
    uploaded_file.seek(0)
    dammit = UnicodeDammit(uploaded_file.read(), ['utf-8', 'windows-1252', 'ascii'])

    uploaded_file.seek(0)

    data = pd.read_csv(uploaded_file,
                       encoding=dammit.original_encoding,
                       **spectra_params)

    if meta_params is not None:
        uploaded_file.seek(0)
        metadata = pd.read_csv(uploaded_file,
                               encoding=dammit.original_encoding,
                               **meta_params)
        return data, metadata
    return data


def choosing_regression_degree(col='default'):
    """
    Slider, choose your polynomial regression degree
    :param name: Str
    :param col: Str
    :return: Int, degree for polynomial regression
    """
    label = 'Polynominal degree'
    val = st.slider(label,
                    min_value=1,
                    max_value=20,
                    value=5,
                    key=f'{col}_deg')
    return int(val)


def choosing_smoothening_window(col='default'):
    """
    Slider, choose window for rolling function for smoothing the spectra
    :param name: Str
    :param col: Str
    :return: Int, window for smoothening
    """
    label = 'Smoothing window'
    val = st.slider(label,
                    min_value=1,
                    max_value=20,
                    value=3,
                    key=f'{col}_window')
    return int(val)


def choosing_trim_range(df):
    min_, max_ = float(df.index.min()), float(df.index.max())
    # min_rs, max_rs = st.slider('Custom range',
    min_max = st.slider('Custom range',
                        min_value=min_, max_value=max_, value=[min_, max_]
                        )
    min_rs, max_rs = min_max.split('__')
    min_rs, max_rs = float(min_rs), float(max_rs)
    return min_rs, max_rs


# @st.cache
def subtract_baseline(df, deg, key=None, model=None):
    """
    Takes DataFrame of spectrum, and correct its baseline by changing the values.
    :param df: DataFrame
    :param deg: int
    :param window: int
    :return: DataFrame
    """
    df = df.copy()
    if key == LABELS['SINGLE']:
        df[LABELS['COR']] = df[model] - peakutils.baseline(df[LABELS['BS']], deg)

    elif key == LABELS['MS']:
        df[LABELS['COR']] = df[model] - peakutils.baseline(df[LABELS['BS']], deg)
        df.dropna(inplace=True)  # TODO: why?
    else:
        for col in range(len(df.columns)):
            df.iloc[:, col] = df.iloc[:, col] - peakutils.baseline(df.iloc[:, col], deg)
    return df


def subtract_baseline_series(series, deg):
    """
    Subtracts baseline from plot.
    :param series: Pandas Series, to be manipulated
    :param deg: Degree of polynomial degree for the baseline correction
    :return: Pandas Series, after correction
    """
    return series - peakutils.baseline(series, deg)


@st.cache
def smoothen_the_spectra(df, window, key=None):
    """
    Takes DataFrame of spectrum, and correct its baseline by changing the values.
    :param df: DataFrame
    :param window: int - tells how many items to take into 'rolling' function
    :param key: String - tells if it should process Single data or other
    :return: DataFrame
    """
    df = df.copy()

    if key == LABELS['SINGLE'] or key == LABELS['MS']:
        df[LABELS['FLAT']] = df[LABELS['COR']].rolling(window=window).mean()

    else:
        df = df.rolling(window=window).mean()

    df.dropna(inplace=True)
    return df


@st.cache
def normalize_spectrum(df, col):
    """
    Takes DataFrame and normalizes data to the range of 0-1
    :param df: DataFrame
    :param col: int or str
    :return: DataFrame
    """
    # For name of col it uses this part
    if type(col) == str:
        return (df.loc[:, col] - df.loc[:, col].min()) / (df.loc[:, col].max() - df.loc[:, col].min())
    elif col is None:
        return (df - df.min()) / (df.max() - df.min())
    # For index  of col it uses this part
    else:
        return (df.iloc[:, col] - df.iloc[:, col].min()) / (df.iloc[:, col].max() - df.iloc[:, col].min())


def normalize_spectrum_series(ser):
    min_, max_ = ser.min(), ser.max()
    return (ser - min_) / (max_ - min_)


@st.cache
def download_button(object_to_download, download_filename, button_text, pickle_it=False):
    """
    Generates a link to download the given object_to_download.

    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.

    Returns:
    -------
    (str): the anchor tag to download object_to_download

    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')

    """
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None

    else:
        if isinstance(object_to_download, bytes):
            ...

        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    prim_color = st.config.get_option('theme.primaryColor')
    bg_color = st.config.get_option('theme.backgroundColor')
    sbg_color = st.config.get_option('theme.secondaryBackgroundColor')
    txt_color = st.config.get_option('theme.textColor')
    font = st.config.get_option('theme.font')

    custom_css = f"""
        <style>
            #{button_id} {{
                background-color: {bg_color};
                color: {txt_color};
                padding: 0.25rem 0.75rem;
                position: relative;
                line-height: 1.6;
                border-radius: 0.25rem;
                border-width: 1px;
                border-style: solid;
                border-color: {bg_color};
                border-image: initial;
                filter: brightness(95%);
                justify-content: center;
                margin: 0px;
                width: auto;
                appearance: button;
                display: inline-flex;
                family-font: {font};
                font-weight: 400;
                letter-spacing: normal;
                word-spacing: normal;
                text-align: center;
                text-rendering: auto;
                text-transform: none;
                text-indent: 0px;
                text-shadow: none;
                text-decoration: none;
            }}
            #{button_id}:hover {{
                
                border-color: {prim_color};
                color: {prim_color};
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: {prim_color};
                color: {sbg_color};
                }}
        </style> """

    dl_link = custom_css + f'<a download="{download_filename}" class= "" id="{button_id}" ' \
                           f'href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'

    return dl_link


def file_to_buffer(filepath):
    """
    Takes data from file under given path
    :param filepath: Str
    :return: StringIO object
    """
    with open(filepath) as f:
        content = f.read()
    buffer = io.StringIO(content)
    buffer.name = os.path.basename(filepath)
    return buffer


@st.cache(hash_funcs={io.StringIO: id})
def load_example_files(spectrometer):
    """
    Loads example files from server
    :param spectrometer: Str, name of chosen spectrometer
    :return: StringIO object, contains of uploaded files
    """
    examples = {
        'BWTEK': ['data/data_examples/bwtek/bwtek(2).txt',
                  'data/data_examples/bwtek/bwtek(3).txt'],
    
        'RENI': ['data/data_examples/renishaw/renishaw(5).txt',
                 'data/data_examples/renishaw/renishaw(6).txt'],
    
        'WITEC': ['data/data_examples/witec/WITec(5).csv',
                  'data/data_examples/witec/WITec(7).csv'],
    
        'WASATCH': ['data/data_examples/wasatch/SERSitive_next_day_1ppm-20201009-093810-270034-WP-00702.csv',
                    'data/data_examples/wasatch/SERSitive_next_day_2ppm-20201009-093705-137238-WP-00702.csv'],
    
        'TELEDYNE': ['data/data_examples/teledyne/teledyne(1).csv',
                     'data/data_examples/teledyne/teledyne(2).csv'],
    
        'JOBIN': ['data/data_examples/jobin_yvon/4MPBA_9B22_10s_1x.txt',
                  'data/data_examples/jobin_yvon/5MPBA_9B22_10s_1x.txt',
                  'data/data_examples/jobin_yvon/6MPBA_9B22_10s_3x.txt',
                  ]
    }

    files = [file_to_buffer(f) for f in examples[spectrometer]]
    return files
