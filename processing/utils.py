import io
import os.path

import numpy as np
import pandas as pd
import peakutils
import streamlit as st
from bs4 import UnicodeDammit



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


def align_spectra(frames):
    """
    Merges single-spectrum DataFrames (Raman Shift as index) into one DataFrame without losing resolution.
    If all spectra share the same Raman Shift values they are simply joined. Otherwise every spectrum is
    linearly interpolated onto the grid of the first spectrum, limited to the range covered by all of them.
    :param frames: List of DataFrames
    :return: DataFrame
    """
    frames = [f[~f.index.duplicated()].sort_index() for f in frames]
    first_index = frames[0].index

    if all(f.index.equals(first_index) for f in frames):
        return pd.concat(frames, axis=1)

    low = max(f.index.min() for f in frames)
    high = min(f.index.max() for f in frames)
    grid = first_index[(first_index >= low) & (first_index <= high)]

    aligned = {}
    for f in frames:
        for col in f.columns:
            aligned[col] = np.interp(grid, f.index.to_numpy(dtype=float), f[col].to_numpy(dtype=float))

    return pd.DataFrame(aligned, index=grid)


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


def subtract_baseline(df, deg):
    """
    Subtracts polynomial baseline from every spectrum (column) of the DataFrame.
    :param df: DataFrame
    :param deg: int, polynomial degree
    :return: DataFrame
    """
    df = df.astype(float)
    for col in df.columns:
        df[col] = df[col] - peakutils.baseline(df[col].to_numpy(), deg)
    return df


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
