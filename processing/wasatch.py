import pandas as pd

from . import utils

RS = 'Raman Shift'


def read_spectrum_wasatch(file_name, separator=','):
    """
    Reads numeric data from file and creates DataFrame
    :param file_name: String
    :return: DataFrame
    """
    df = pd.read_csv(file_name, sep=f'{separator}', decimal='.', skipinitialspace=True, encoding='utf-8')
    df = df.rename(columns={df.columns[0]: RS})
    df.dropna(inplace=True, how='any', axis=0)
    df.dropna(inplace=True, axis=1)
    df = df.loc[:, ~df.columns.duplicated()]
    df.set_index(RS, inplace=True)
    return df


def read_data_metadata_wasatch(uploaded_files, separator):
    temp_data_df = {}
    # Iterates through each file, converts it to DataFrame and adds to temporary dictionary
    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        # read data and adds it to temp Dict
        data = utils.read_spec(uploaded_file, separator)
        temp_data_df[uploaded_file.name[:-4]] = data
    return temp_data_df
