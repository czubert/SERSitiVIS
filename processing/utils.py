import glob
import re
import peakutils
import pandas as pd
import streamlit as st
from collections import Counter

from . import separate

RS = 'Raman Shift'
DS = 'Dark Subtracted #1'
BS = 'Baseline'


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


@st.cache
def group_dfs(data_dfs):
    """
    Returns dict consists of one DataFrame per data type, other consists of mean values per data type.
    :param data_dfs: Dict
    :return: DataFrame
    """

    # groups Dark Subtracted column from all dfs to one and overwrites data df in dictionary
    if isinstance(data_dfs, dict):
        df = pd.concat([data_df for data_df in data_dfs.values()], axis=1)
    elif isinstance(data_dfs, list):
        df = pd.concat([data_df for data_df in data_dfs], axis=1)

    df.dropna(axis=1, inplace=True, how='all')  # drops columns filled with NaN values

    return df


def show_dataframe(df, key):
    if st.button(f'Show data', key=key):
        st.dataframe(df)


def upload_file():
    """
    Shows Streamlits widget to upload files
    :return: File
    """
    return st.file_uploader('Upload txt spectra')


def read_data_metadata(uploaded_files):
    temp_data_df = []
    temp_meta_df = []

    # Iterates through each file, converts it to DataFrame and adds to temporary dictionary
    for uploaded_file in uploaded_files:
        # read data and adds it to temp Dict
        data = separate.read_spectrum(uploaded_file)
        temp_data_df.append(data)

        # Resets file buffer so you can read and use it again
        uploaded_file.seek(0)

        # read metadata and adds it to temp Dict
        meta = separate.read_metadata(uploaded_file)
        temp_meta_df.append(meta)

    return temp_data_df, temp_meta_df


def correct_baseline(df, deg):
    df2 = df.copy()
    for col in range(len(df.columns)):
        df2.iloc[:, col] = df.iloc[:, col] - peakutils.baseline(df.iloc[:, col], deg)

    return df2


def correct_baseline_single(df, deg):
    df2 = df.copy()
    df2['Corrected'] = df2[DS] - peakutils.baseline(df2[BS], deg)

    return df2
