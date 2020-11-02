from . import utils

RS = 'Raman Shift'


def read_witec(uploaded_files, separator=','):
    """
    Read data and adds it to temp Dict
    :param file_name: String
    :return: Dict of DataFrames
    """

    temp_data_df = {}

    spectra_params = {'sep': separator, 'decimal': '.', 'skipinitialspace': True, 'encoding': 'utf-8'}

    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)

        data = utils.read_spec(uploaded_file, spectra_params)
        data = data.rename(columns={data.columns[0]: RS})

        # cleaning data
        data.dropna(inplace=True, how='any', axis=0)
        data.dropna(inplace=True, axis=1)
        data = data.loc[:, ~data.columns.duplicated()]

        data.set_index(RS, inplace=True)

        temp_data_df[uploaded_file.name[:-4]] = data

    return temp_data_df
