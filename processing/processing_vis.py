import pandas as pd

"""
Module responsible for processing data for visualisation 
"""


def group_dfs(separated_metadata_data_dfs):
    """
    Returns dict consists of one DataFrame per data type, other consists of mean values per data type.
    :param separated_metadata_data_dfs: dict
    :return: dict
    """
    # groups Dark Subtracted column from all dfs to one and overwrites data df in dictionary
    grouped_df = {}
    for substrate_type in separated_metadata_data_dfs.keys():
        df = pd.concat([data_df[1] for data_df in separated_metadata_data_dfs[substrate_type]], axis=1)
        df.dropna(axis=1, inplace=True, how='all')  # drops columns filled with NaN values
        df.dropna(axis=0, inplace=True)  # drops indices with any NaN values
        df.reset_index(inplace=True)
        grouped_df[substrate_type] = df

    return grouped_df


def mean_std(grouped_data_df):
    """
    Calculate mean values of all spectra for given substrate type and returns new data frame
    with columns of mean and std
    :param grouped_data_df: Dictionary
    :return: Dictionary
    """
    mean_std_dfs = {}
    for substrate_type in grouped_data_df.keys():
        mean_std_dfs[substrate_type] = mean_for_grouped_dfs(grouped_data_df[substrate_type])

    return mean_std_dfs


def mean_for_grouped_dfs(dfs):
    """
    Calculates mean and std values and returns Data Frame with this values
    :param dfs: Data Frame
    :return: Data Frame
    """
    df = pd.DataFrame()
    df['Raman Shift'] = dfs['Raman Shift']
    df['Average'] = dfs.mean(axis=1)
    df['Average_err'] = dfs.std(axis=1)
    return df


if __name__ == '__main__':
    url = '../data/*/*.txt'
