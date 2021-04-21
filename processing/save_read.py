import os

import pandas as pd
import streamlit as st
from joblib import dump, load


# PATH = 'data_output'


def save_as_joblib(data_to_save, file_name, path):
    if not os.path.isdir(f'{path}'):
        os.makedirs(f'{path}')

    dump(data_to_save, f'{path}/{file_name}.joblib')


def read_joblib(file_name, dir_name):
    return load(f'{dir_name}/{file_name}.joblib')


def save_as_csv(data, file_name, dir_name):
    if not os.path.isdir(f'{dir_name}'):
        os.mkdir(f'{dir_name}')
    
    data.to_csv(f'{dir_name}/{file_name}.csv')


def read_csv(file_name, dir_name):
    return pd.read_csv(f'{dir_name}/{file_name}.csv')


def save_adj_spectra_to_file(df_to_save, file_name, key='default'):
    from processing.utils import download_button
    # User can set custom name for a file to write
    input_file_name = st.text_input(
        'Enter the name of the file to save (if not given it will be added automatically based on the name of the file)',
        key=key)
    
    # Checks if user have set a file name if not, it will be default
    if input_file_name:
        file_name = input_file_name
    else:
        file_name += '_SERSitiVIS_spectra'
    tmp_download_link = download_button(df_to_save.reset_index(), f'{file_name}.csv',
                                        button_text='Click here to download your text!')
    
    st.markdown(tmp_download_link, unsafe_allow_html=True)
