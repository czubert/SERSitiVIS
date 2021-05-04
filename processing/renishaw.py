import pandas as pd

from . import utils

RS = 'Raman Shift'


def read_renishaw(uploaded_files, separator):
    """
    Reads numeric data from file and creates DataFrame
    :param uploaded_file: Streamlit uploader file
    :return: Dict of DataFrames
    """
    reni_data = {}

    spectra_params = {'sep': separator, 'decimal': '.', 'skipinitialspace': True, 'encoding': 'utf-8',
                      'header': None}

    # Iterates through each file, converts it to DataFrame and adds to temporary dictionary
    for uploaded_file in uploaded_files:
        data = utils.read_spec(uploaded_file, spectra_params)

        name = uploaded_file.name[:-4]

        data.dropna(inplace=True, how='any', axis=0)
        data.columns = [RS, name]
        data[RS] = data[RS].round(decimals=0)
        data.set_index(RS, inplace=True)

        reni_data[uploaded_file.name[:-4]] = data
    
    df = pd.concat([reni_data[data_df] for data_df in reni_data], axis=1)
    df.dropna(inplace=True, how='any', axis=0)
    
    return df
