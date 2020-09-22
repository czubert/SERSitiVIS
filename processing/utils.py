import glob
import re
import peakutils
import pandas as pd
import streamlit as st
from collections import Counter

import plotly.graph_objects as go
import plotly.express as px

from . import separate

RS = 'Raman Shift'
DS = 'Dark Subtracted #1'


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
    Returns dict consists of one DataFrame per data type, other consists of mean values per data type.
    :param data_dfs: Dict
    :return: DataFrame
    """

    # groups Dark Subtracted column from all dfs to one and overwrites data df in dictionary
    if isinstance(data_dfs, dict):
        df = pd.concat([data_df for data_df in data_dfs.values()], axis=1)
    elif isinstance(data_dfs, list):
        df = pd.concat([data_df for data_df in data_dfs], axis=1)

    # df.reset_index(inplace=True)
    df.dropna(axis=1, inplace=True, how='all')  # drops columns filled with NaN values
    df.dropna(axis=0, inplace=True)  # drops indices with any NaN values

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


def fig_layout(template, fig, descr='Chosen spectra'):
    # changing layout and styles

    fig.update_layout(title=descr,
                      template=template,
                      title_font_size=20,
                      width=950,
                      height=590,
                      xaxis=dict(
                          title=f"{RS} [cm^-1]",
                          linecolor="#BCCCDC",  # Sets color of X-axis line
                          showgrid=False  # Removes X-axis grid lines
                      ),
                      yaxis=dict(
                          title="Intensity",
                          linecolor="#BCCCDC",  # Sets color of Y-axis line
                          showgrid=True,  # Removes Y-axis grid lines
                      ),
                      legend=go.layout.Legend(x=0.5, y=-0.2, traceorder="normal",
                                              font=dict(
                                                  family="sans-serif",
                                                  size=10,
                                                  color="black"
                                              ),
                                              bgcolor="#fff",
                                              bordercolor="#ccc",
                                              borderwidth=0.4,
                                              orientation='h',
                                              xanchor='auto',
                                              itemclick='toggle',

                                              )),

    return fig


def draw_plot(df, x, y, plot_color, color='variable'):
    """
    # dictionary of tuples of dfs separated corresponding to the type of substrate
    :param df: DataFrame
    :return: Plotly object - Figure
    """

    fig = px.line(df, x=x, y=y, color=color,
                  color_discrete_sequence=plot_color)
    #
    # fig = px.line(df, x=x, y=y, color=color,
    #               color_discrete_sequence=px.colors.cyclical.IceFire)

    return fig


def choose_template():
    template = st.radio(
        "Choose chart template",
        ('ggplot2', 'seaborn', 'simple_white', 'plotly',
         'plotly_white', 'plotly_dark', 'presentation', 'xgridoff',
         'ygridoff', 'gridon', 'none'), index=1, key='new')
    return template


def plot_color():
    colors = {
        'Plotly': px.colors.qualitative.Plotly,
        'Vivid': px.colors.qualitative.Vivid,
        'Safe': px.colors.qualitative.Safe,
        'Prism': px.colors.qualitative.Prism,
        'Pastel': px.colors.qualitative.Pastel,
        'Bold': px.colors.qualitative.Bold,
        'Antique': px.colors.qualitative.Antique,
        'Set1': px.colors.qualitative.Set1,
        'Set2': px.colors.qualitative.Set2,
        'Set3': px.colors.qualitative.Set3,
        'Pastel2': px.colors.qualitative.Pastel2,
        'Dark2': px.colors.qualitative.Dark2,
        'Pastel1': px.colors.qualitative.Pastel1,
        'Light24': px.colors.qualitative.Light24,
        'Dark24': px.colors.qualitative.Dark24,
        'Alphabet': px.colors.qualitative.Alphabet,
        'T10': px.colors.qualitative.T10,
        'G10': px.colors.qualitative.G10,
        'D3': px.colors.qualitative.D3
    }

    plot_color = st.radio(
        "Choose set of colors for spectra",
        ('Plotly', 'Vivid', 'Safe', 'Prism', 'Pastel', 'Bold', 'Antique', 'Set3', 'Pastel2', 'Set2', 'Dark2', 'Pastel1',
         'Set1', 'Light24', 'Dark24', 'Alphabet', 'T10', 'G10', 'D3'), index=1)

    return colors[plot_color]
