import pandas as pd

from constants import LABELS
from . import utils


def read_bwtek(uploaded_files, delim):
    spectra_params = {'sep': delim,
                      # 'skiprows': lambda x: x < 79,
                      'decimal': ',',
                      'usecols': ['Pixel', LABELS["RS"], LABELS["DS"]],
                      'skipinitialspace': True}
    
    meta_params = {'sep': delim,
                   # 'skiprows': lambda x: x > 78,
                   'decimal': ',', 'index_col': 0,
                   'skipinitialspace': True, 'header': None}
    
    temp_data_df = {}
    temp_meta_df = {}
    
    for uploaded_file in uploaded_files:
        data, metadata = utils.read_spec(uploaded_file, spectra_params, meta_params)
        
        data = data[data.loc[:, 'Pixel'] > 310]
        data.set_index('Pixel', inplace=True)
        
        data.dropna(inplace=True, how='any', axis=0)

        data.rename(columns={LABELS["DS"]: uploaded_file.name[:-4]}, inplace=True)
        data.set_index('Raman Shift', inplace=True)

        temp_data_df[uploaded_file.name] = data
        temp_meta_df[uploaded_file.name] = metadata

    # concatenating all updated spectra into one DataFrame
    df = pd.concat([data_df for data_df in temp_data_df.values()], axis=1)

    # concatenating all updated spectras metadata into one DataFrame
    df_metadata = pd.concat([metadata for metadata in temp_meta_df.values()], axis=1)

    # dropping NaN values
    df.dropna(axis=1, inplace=True, how='all')

    return df, df_metadata
