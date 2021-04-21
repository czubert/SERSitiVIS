import base64
import glob
import io
import json
import os.path
import pickle
import re
import uuid
from collections import Counter

import pandas as pd
import peakutils
import streamlit as st

RS = 'Raman Shift'
COR = 'Corrected'
DS = 'Dark Subtracted #1'
BS = 'Baseline'
MS = 'Mean spectrum'
AV = 'Average'


def get_names(url):
    """
    Creates list of strings of files paths
    :param url: String
    :return: List
    """
    file_names = glob.glob(url)
    return file_names


def lower_names(file_names):
    """
    Takes list of strings and makes characters lower
    :param file_names: List
    :return: List
    """

    file_names_lower = [x.lower() for x in file_names]
    return file_names_lower


def pattern_in_name(name, re_pattern):
    if re.search(re_pattern, name) is None:
        return False
    elif re.search(re_pattern, name) is not None:
        return True


def save_df_to_csv(df, path):
    df.to_csv(f'{path}')


def read_df_from_csv(path):
    return pd.read_csv(f'{path}')


def reduce_list_dimension(dic):
    sep_names = dic.values()
    sep_names_chain = []
    for el in sep_names:
        sep_names_chain += el

    return sep_names_chain


def check_for_repetitions(list1, list2):
    res = list((Counter(list1) - Counter(list2)).elements())

    return res


def check_for_differences(list1, list2):
    counter = abs(len(list2) - len(list1))

    return counter


def group_dfs(data_dfs):
    """
    Returned dict consists of one DataFrame per data type, other consists of mean values per data type.
    :param data_dfs: Dict
    :return: DataFrame
    """
    # groups Dark Subtracted column from all dfs to one and overwrites data df in dictionary
    df = pd.concat([data_df for data_df in data_dfs.values()], axis=1)
    df.dropna(axis=1, inplace=True, how='all')  # drops columns filled with NaN values

    return df


def upload_file():
    """
    Shows Streamlits widget to upload files
    :return: File
    """
    return st.file_uploader('Upload txt spectra')


def read_spec(uploaded_file, spectra_params, meta_params=None):
    uploaded_file.seek(0)
    data = pd.read_csv(uploaded_file, **spectra_params)

    if meta_params is not None:
        uploaded_file.seek(0)
        metadata = pd.read_csv(uploaded_file, **meta_params)
        return data, metadata

    return data


def correct_baseline(df, deg, window):
    df2 = df.copy()
    for col in range(len(df.columns)):
        df2.iloc[:, col] = df.iloc[:, col] - peakutils.baseline(df.iloc[:, col], deg)
        df2.iloc[:, col] = df2.iloc[:, col].rolling(window=window).mean()

    return df2


def correct_baseline_single(df, deg, model=DS):
    df2 = df.copy()
    if model == DS:
        df2[COR] = df2[DS] - peakutils.baseline(df2[BS], deg)
    elif model == MS:
        df2[COR] = df2[AV] - peakutils.baseline(df2[BS], deg)
    else:
        df2[COR] = df2[model] - peakutils.baseline(df2[BS], deg)
    
    return df2


def normalize_spectra(df, col):
    """
    Takes DataFrame and normalizes data to the range of 0-1
    :param df: DataFrame
    :param col: int or str
    :return: DataFrame
    """
    # For name of col it uses this part
    if type(col) == str:
        return (df.loc[:, col] - df.loc[:, col].min()) / (df.loc[:, col].max() - df.loc[:, col].min())
    # For index  of col it uses this part
    else:
        return (df.iloc[:, col] - df.iloc[:, col].min()) / (df.iloc[:, col].max() - df.iloc[:, col].min())


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
            pass

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
                filter: brightness(105%);
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
    with open(filepath) as f:
        content = f.read()
    buffer = io.StringIO(content)
    buffer.name = os.path.basename(filepath)
    return buffer


@st.cache(hash_funcs={io.StringIO: id})
def load_example_files(spectrometer):
    examples = {
        'BWTEK': ['data_examples/bwtek/bwtek(2).txt', 'data_examples/bwtek/bwtek(3).txt'],
        'Renishaw': ['data_examples/renishaw/renishaw(5).txt', 'data_examples/renishaw/renishaw(6).txt'],
        'WITec Alpha300 R+': ['data_examples/witec/WITec(4).csv', 'data_examples/witec/WITec(5).csv'],
        'Wasatch System': ['data_examples/wasatch/SERSitive_next_day_1ppm-20201009-093810-270034-WP-00702.csv',
                           'data_examples/wasatch/SERSitive_next_day_2ppm-20201009-093705-137238-WP-00702.csv'],
        'Teledyne Princeton Instruments': [],
    }

    files = [file_to_buffer(f) for f in examples[spectrometer]]
    return files
