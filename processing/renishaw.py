import pandas as pd

from constants import LABELS
from . import utils


def read_renishaw(uploaded_files, delim):
    """
    Reads numeric data from file and creates DataFrame
    :param uploaded_file: Streamlit uploader file
    :return: Dict of DataFrames
    """
    reni_data = {}
    spectra_params_uploaded = {'sep': delim, 'decimal': '.', 'skipinitialspace': True,
                               'header': None}
    
    # Iterates through each file, converts it to DataFrame and adds to temporary dictionary
    for uploaded_file in uploaded_files:
        # TODO nie wiem, czemu nie dziala \t dla wszystkich renishawowych danych...
        data = utils.read_spec(uploaded_file, spectra_params_uploaded)
        
        name = uploaded_file.name[:-4]
        data.dropna(inplace=True, how='any', axis=0)
        data.columns = [LABELS["RS"], name]
        data[LABELS["RS"]] = data[LABELS["RS"]].round(decimals=0)
        data.set_index(LABELS["RS"], inplace=True)
        
        reni_data[uploaded_file.name[:-4]] = data
    
    df = pd.concat([reni_data[data_df] for data_df in reni_data], axis=1)
    df.dropna(inplace=True, how='any', axis=0)
    
    return df
