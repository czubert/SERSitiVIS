import pandas as pd

"""
Module responsible for data selection 
"""
RS = 'Raman Shift'
DS = 'Dark Subtracted #1'

path_name = 'data_output/tmp_separated_data'
file_name = 'separated_data'


def read_spectrum(file):
    """
    Reads numeric data from file and creates DataFrame
    :param file: String
    :return: DataFrame
    """
    read_params = {'sep': ';', 'skiprows': lambda x: x < 79 or x > 1500, 'decimal': ',',
                   'usecols': ['Pixel', RS, DS],
                   'skipinitialspace': True, 'encoding': "utf-8"}

    df = pd.read_csv(file, **read_params)

    df = df[df.loc[:, 'Pixel'] > 310]
    df.set_index('Pixel', inplace=True)

    # TODO delete it later
    df.dropna(inplace=True, how='any', axis=0)

    df.rename(columns={DS: file.name[:-4]}, inplace=True)
    df.set_index('Raman Shift', inplace=True)

    return df


def read_spectrum_renishaw(uploaded_file, separator):
    """
    Reads numeric data from file and creates DataFrame
    :param uploaded_file: String
    :return: DataFrame
    """

    name = uploaded_file.name[:-4]
    df = pd.read_csv(uploaded_file, sep=f'{separator}', decimal='.', skipinitialspace=True, encoding='utf-8',
                     header=None)
    df.dropna(inplace=True, how='any', axis=0)
    df.columns = [RS, name]
    df[RS] = df[RS].round(decimals=0)
    df.set_index(RS, inplace=True)

    return df


def read_spectrum_xy(file_name, separator=','):
    """
    Reads numeric data from file and creates DataFrame
    :param file_name: String
    :return: DataFrame
    """
    df = pd.read_csv(file_name, sep=f'{separator}', decimal='.', skipinitialspace=True, encoding='utf-8')
    # df = df.rename(columns=lambda x: re.sub('.*[U].*', RS, x))
    df = df.rename(columns={df.columns[0]: RS})
    df.dropna(inplace=True, how='any', axis=0)
    df.dropna(inplace=True, axis=1)
    df = df.loc[:, ~df.columns.duplicated()]
    df.set_index(RS, inplace=True)
    return df


def read_metadata(filepath):
    """
    Reads metadata from file and creates DataFrame
    :param filepath: String
    :return: data frame
    """

    read_params = {'sep': ';', 'skiprows': lambda x: x > 78, 'decimal': ',', 'index_col': 0,
                   'skipinitialspace': True, 'encoding': "utf-8", 'header': None}

    df = pd.read_csv(filepath, **read_params)

    return df
