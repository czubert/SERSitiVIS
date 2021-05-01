import pandas as pd

from . import utils

RS = 'Raman Shift'


def read_witec(uploaded_files, separator=','):
    """
    Read data and adds it to temp Dict
    :param file_name: String
    :return: Dict of DataFrames
    """
    
    temp_data_df = {}
    
    spectra_params = {'sep': separator, 'decimal': '.', 'skipinitialspace': True, 'encoding': 'utf-8', 'header': 0}
    
    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        tmp_data = pd.DataFrame()
        data = utils.read_spec(uploaded_file, spectra_params)
        
        tmp_data[RS] = data.iloc[:, 0]
        
        # TODO it does not work properly, it shows that two unequal columns are equal
        for idx in range(len(data.columns) - 1):
            if (data.iloc[:, 0] != data.iloc[:, idx + 1]).all() and 'Unnamed' not in data.columns[idx + 1]:
                tmp_data[data.columns[idx + 1]] = data.iloc[:, idx + 1]
        
        # cleaning data
        tmp_data.dropna(inplace=True, how='any', axis=0)
        tmp_data.dropna(inplace=True, axis=1)
        tmp_data = tmp_data.loc[:, ~tmp_data.columns.duplicated()]
        
        # setting Raman Shift as index
        tmp_data.set_index(RS, inplace=True)
        
        # saving data into dictionary
        temp_data_df[uploaded_file.name[:-4]] = tmp_data
    
    return temp_data_df
