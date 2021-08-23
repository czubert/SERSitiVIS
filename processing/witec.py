import pandas as pd

from constants import LABELS
from . import utils


def read_witec(uploaded_files, separator=','):
    """
    Read data and adds it to temp Dict
    :param file_name: String
    :return: Dict of DataFrames
    """
    
    all_uploaded_witek_data_files = {}
    df = pd.DataFrame()
    import streamlit as st
    
    spectra_params = {'sep': separator, 'decimal': '.', 'skipinitialspace': True, 'header': 0}
    
    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        single_uploaded_data_file = pd.DataFrame()
        data = utils.read_spec(uploaded_file, spectra_params)
    
        single_uploaded_data_file[LABELS["RS"]] = data.iloc[:, 0]
    
        cols = {f'{uploaded_file.name[:-4]} ({col})': col for col in data.columns if not col.startswith('Unnamed') if
                not col.startswith(LABELS['RS'])}
    
        single_uploaded_data_file[list(cols.keys())] = data[list(cols.values())]
    
        # cleaning data
        single_uploaded_data_file.dropna(inplace=True, how='any', axis=0)
        single_uploaded_data_file.dropna(inplace=True, axis=1)
        single_uploaded_data_file = single_uploaded_data_file.loc[:, ~single_uploaded_data_file.columns.duplicated()]
    
        # setting Raman Shift as index
        single_uploaded_data_file.set_index(LABELS["RS"], inplace=True)
    
        # saving data into dictionary
        all_uploaded_witek_data_files[uploaded_file.name[:-4]] = single_uploaded_data_file

    df = pd.concat([all_uploaded_witek_data_files[data_df] for data_df in all_uploaded_witek_data_files], axis=1)
    return df
