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

LABELS = {'SINGLE': 'Single spectra', 'MS': "Mean spectrum", 'GS': "Grouped spectra", 'P3D': "Plot 3D",
          'AV': "Average", 'BS': "Baseline", 'RS': "Raman Shift", 'DS': "Dark Subtracted #1",
          'DEG': "Polynominal degree", 'WINDOW': "Set window for spectra flattening",
          'DFS': {'ML model grouped spectra': 'Dark Subtracted #1', 'ML model mean spectra': 'Average'},
          'FLAT': "Flattened", 'COR': "Corrected", 'ORG': "Original spectrum", 'RAW': "Raw Data",
          'OPT': "Optimised Data", 'NORM': "Normalized", 'OPT_S': "Optimised Spectrum", }


@st.cache
def read_spec(uploaded_file, spectra_params, meta_params=None):
    """
    Reads csv file and returns it, if metadata available returns also metadata
    :param uploaded_file: csv file
    :param spectra_params: Dict
    :param meta_params: Dict
    :return: DataFrame
    """
    uploaded_file.seek(0)
    data = pd.read_csv(uploaded_file, **spectra_params)
    
    if meta_params is not None:
        uploaded_file.seek(0)
        metadata = pd.read_csv(uploaded_file, **meta_params)
        return data, metadata
    
    return data


def degree_and_window_sliders(name='all uploaded', col='default'):
    """
    Shows sliders in streamlit to let user adjust the degree of polinomial regression, and window for smoothening
    :param col: int - Just to make it possible to use multiple sliders at one 'site' of the website
    :return: int, int
    """
    
    deg = st.slider(f'{"Polynominal degree"} for {name} spectra', min_value=1, max_value=20, value=5,
                    key=f'{col}_deg')
    
    window = st.slider(f'{"Set window for spectra flattening"} for {name} spectra', min_value=1, max_value=20,
                       value=3,
                       key=f'{col}_window')
    return deg, window


@st.cache
def process_grouped_opt_spec(df2, spectra_conversion_type, col, deg, window):
    """
    Corrects baseline, flattens the plot and if 'normalized' is chosen, then it normalize data
    :param df2: DataFrame
    :param spectra_conversion_type: str
    :param col: str
    :param deg: int
    :param window: int, float
    :return: DataFrame
    """
    corrected = pd.DataFrame(df2.loc[:, col]).dropna()

    if spectra_conversion_type == 'Normalized':
        normalized_df2 = normalize_spectra(df2, col)
        corrected = pd.DataFrame(normalized_df2).dropna()

    corrected = smoothen_the_spectra(corrected, window=window)

    return subtract_baseline(corrected, deg).dropna()


@st.cache
def subtract_baseline(df, deg, key=None, model=None):
    """
    Takes DataFrame of spectrum, and correct its baseline by changing the values.
    :param df: DataFrame
    :param deg: int
    :param window: int
    :return: DataFrame
    """
    df2 = df.copy()
    if key == LABELS['SINGLE']:
        df2[LABELS['COR']] = df2[model] - peakutils.baseline(df2[LABELS['BS']], deg)
    
    elif key == LABELS['MS']:
        df2[LABELS['COR']] = df2[model] - peakutils.baseline(df2[LABELS['BS']], deg)
        df2.dropna(inplace=True)
    
    else:
        for col in range(len(df.columns)):
            df2.iloc[:, col] = df.iloc[:, col] - peakutils.baseline(df.iloc[:, col], deg)
    
    return df2


@st.cache
def smoothen_the_spectra(df, window, key=None):
    """
    Takes DataFrame of spectrum, and correct its baseline by changing the values.
    :param df: DataFrame
    :param window: int - tells how many items to take into 'rolling' function
    :param key: String - tells if it should process Single data or other
    :return: DataFrame
    """
    df2 = df.copy()
    
    if key == LABELS['SINGLE']:
        df2[LABELS['FLAT']] = df2[LABELS['COR']].rolling(window=window).mean()
    elif key == LABELS['MS']:
        df2[LABELS['FLAT']] = df2[LABELS['AV']].rolling(window=window).mean()
    else:
        for col in range(len(df.columns)):
            df2.iloc[:, col] = df2.iloc[:, col].rolling(window=window).mean()
    
    df2.dropna(inplace=True)
    return df2


@st.cache
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
