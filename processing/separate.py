import os
import pandas as pd
import streamlit as st

from processing import save_read, utils

"""
Module responsible for data selection 
"""

path_name = 'data_output/tmp_separated_data'
file_name = 'separated_data'


@st.cache(suppress_st_warning=True)
def separate_type(url, processing_type=None):
    """
    Separates data to 4 groups, two are background spectra of ag and au substrates,
    other two are spectra of analyte that is our standard to check the performance of the substrates,
    on both ag and au substrates. Returns List of sets with metadata and data,
    that has parameter name that corresponds to it's properties - ag, au, ag_bg, au_bg
    :param url: String
    :return: Dictionary
    """

    # get names
    names = utils.get_names(url)

    # lowercase file names
    names_lower = set(utils.lower_names(names))

    # creates a dictionary where type of substrate is a key and list of relevant file names is a value
    split_names, not_assigned_spectra = split_substr_types(names_lower)

    # changing values of dictionary from list of names to list of tuples of dfs
    metadata_data_dfs = {}
    for substrate_type in split_names.keys():
        metadata_data_dfs[substrate_type] = read_list_of_spectra_files(split_names[substrate_type])

    # dictionary of tuples of dfs separated corresponding to the type of substrate
    if processing_type == 'visualisation':
        return metadata_data_dfs, names_lower, split_names, not_assigned_spectra
    else:
        save_read.save_as_joblib(metadata_data_dfs, file_name, path_name)
        return metadata_data_dfs


@st.cache
def split_substr_types(files_names_lower):
    """
    Creates dictionary in which data is separated into 4 groups: ag, au, ag_bg, au_bg,
    each name of a group is a key in the dictionary. List of corresponding file names are values.
    :param files_names_lower: list
    :return: dictionary
    """
    dictio = {'ag': [], 'au': [], 'tlo ag': [], 'tlo au': []}
    not_assigned_spectra = []

    # WHAT tak wiem, straszny syf, ale sam już nie wiem jak to zrobić, żeby działało
    bg_pattern = r"t[lł][ao]"
    pmba_pattern = r"pmba"
    au_pattern = r"[ g_]au"

    au_bg_pattern = r"t[lł][oa][, _](?!(.*(pod|do au))).*(ag)?_?au"
    ag_bg_pattern = r"t[lł][oa][, _](?!(.*(do|pod))).*ag"

    for name in files_names_lower:
        agau_in_name = utils.pattern_in_name(name, au_pattern)
        bg_in_name = utils.pattern_in_name(name, bg_pattern)
        pmba_in_name = utils.pattern_in_name(name, pmba_pattern)

        # Ag substrates with PMBA analyte
        if not agau_in_name and not bg_in_name and pmba_in_name:
            dictio['ag'].append(name)

        # Au substrates with PMBA analyte
        elif agau_in_name and not bg_in_name and pmba_in_name:
            dictio['au'].append(name)

        # Au substrates background
        elif (utils.pattern_in_name(name, au_bg_pattern)) & (not pmba_in_name):
            dictio['tlo au'].append(name)

        # Ag substrates background
        elif (utils.pattern_in_name(name, ag_bg_pattern)) & (not pmba_in_name):
            dictio['tlo ag'].append(name)

        # Files with wrong names or different analytes
        else:
            not_assigned_spectra.append(name)

    return dictio, not_assigned_spectra


@st.cache
def read_list_of_spectra_files(file_paths_of_one_type):
    """
    Creates list of tuples, where first element of tuple is data frame with metadata,
    second element is data frame with data.
    Additionally it gives corresponding name to the data frame.
    :param file_paths_of_one_type: list
    :return: list of tuples
    """

    data = []

    for file_path in file_paths_of_one_type:
        # Splits path name into two elements in a tuple. One is path and the second is name of a file
        if isinstance(file_path, str):
            path_split = os.path.split(file_path)
            file_name = path_split[1]
        else:
            file_name = file_path

        # adding name of file into metadata DataFrame
        meta_df = read_metadata(file_path)
        meta_df.loc['file_name'] = file_name

        data_df = read_spectrum(file_path)
        data_df.rename(columns={'Dark Subtracted #1': file_name}, inplace=True)

        # creates list of tuples containing 2 elements metadata and data
        data.append((meta_df, data_df))
    return data


def read_spectrum(filepath):
    """
    Reads numeric data from file and creates DataFrame
    :param filepath: String
    :return: DataFrame
    """
    read_params = {'sep': ';', 'skiprows': lambda x: x < 79 or x > 1500, 'decimal': ',',
                   'usecols': ['Pixel', 'Raman Shift', 'Dark Subtracted #1'],
                   'skipinitialspace': True, 'encoding': "utf-8"}
    df = pd.read_csv(filepath, **read_params)

    df = df[df.loc[:, 'Pixel'] >310]
    df.set_index('Pixel', inplace=True)

    # TODO delete it later
    df.dropna(inplace=True, how='any', axis=0)

    df.set_index('Raman Shift', inplace=True)
    return df


def read_spectrum_renishaw(file_name, separator):
    """
    Reads numeric data from file and creates DataFrame
    :param file_name: String
    :return: DataFrame
    """
    df = pd.read_csv(file_name, sep=f'{separator}', decimal='.', skipinitialspace=True, encoding='utf-8', header=None)
    df.dropna(inplace=True, how='any', axis=0)
    df.columns = ['Raman Shift', 'Dark Subtracted #1']
    df['Raman Shift'] = df['Raman Shift'].round(decimals=0)
    df.set_index('Raman Shift', inplace=True)
    return df

def read_spectrum_xy(file_name, separator=','):
    """
    Reads numeric data from file and creates DataFrame
    :param file_name: String
    :return: DataFrame
    """
    import re
    df = pd.read_csv(file_name, sep=f'{separator}', decimal='.', skipinitialspace=True, encoding='utf-8')
    df = df.rename(columns=lambda x: re.sub('.*[Unn].*', 'Raman Shift', x))

    df.dropna(inplace=True, how='any', axis=0)
    df.dropna(inplace=True, axis=1)
    df = df.loc[:, ~df.columns.duplicated()]
    df.set_index('Raman Shift', inplace=True)
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


@st.cache
def duplication_check(split_names, names_lower, not_assigned_spectra):
    """
    Checks if any file was used twice or not. And displays the results on the main screen
    :param split_names: List
    :param names_lower: List
    :param not_assigned_spectra: List
    """

    # reduces dimension of the list so all the differentiated names are in one list ready for comparison
    sep_names_chain = utils.reduce_list_dimension(split_names)

    # checks for repetitions
    repetitions = utils.check_for_repetitions(sep_names_chain, names_lower)

    # checks for differences
    differences = utils.check_for_differences(sep_names_chain, names_lower)

    # Displays repetitions if there are any
    if repetitions:
        st.write(f'Number of repetitions: {len(repetitions)}')
        st.write(f'List of repetitions: {repetitions}')
    else:
        st.write('No repetitions found')

    # list of differences between lists and data frame creation
    df = pd.DataFrame(not_assigned_spectra)

    # Displays differences if there are any
    if not_assigned_spectra:
        st.write('')
        st.write(f'Number of not assigned spectra: {differences}')
        st.write(f'List of not assigned spectra:')
        st.write(df)
    else:
        st.write('All spectra are assigned')


def check_if_data_separated(url):
    # if os.path.isfile(f'../output_data/{dir}/{file_name}.joblib'):
    if os.path.isfile(f'{path_name}/{file_name}.joblib'):
        return save_read.read_joblib(file_name, path_name)
    else:
        return separate_type(url)


if __name__ == '__main__':
    url = '../data/*/*.txt'
