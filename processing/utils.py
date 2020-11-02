import glob
import re
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


def show_dataframe(df, key):
    if st.button(f'Show data', key=key):
        st.dataframe(df)


def upload_file():
    """
    Shows Streamlits widget to upload files
    :return: File
    """
    return st.file_uploader('Upload txt spectra')


def specify_separator(idx):
    return st.sidebar.radio('Specify the separator', ('comma', 'dot', 'tab', 'space'), idx)


def read_spec(uploaded_file, spectra_params, meta_params=None):
    st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
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
