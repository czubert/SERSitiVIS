import pandas as pd

from . import utils

RS = 'Raman Shift'


def read_witec(uploaded_files, separator=','):
    """
    Read data and adds it to temp Dict
    :param file_name: String
    :return: Dict of DataFrames
    """
    
    all_uploaded_witek_data_files = {}
    df = pd.DataFrame()
    
    spectra_params = {'sep': separator, 'decimal': '.', 'skipinitialspace': True, 'encoding': 'utf-8', 'header': 0}
    
    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        single_uploaded_data_file = pd.DataFrame()
        data = utils.read_spec(uploaded_file, spectra_params)
        
        single_uploaded_data_file[RS] = data.iloc[:, 0]
        
        cols = [col for col in data.columns if not col.startswith('Unnamed')]
        single_uploaded_data_file[cols] = data[cols]
        
        # cleaning data
        single_uploaded_data_file.dropna(inplace=True, how='any', axis=0)
        single_uploaded_data_file.dropna(inplace=True, axis=1)
        single_uploaded_data_file = single_uploaded_data_file.loc[:, ~single_uploaded_data_file.columns.duplicated()]
        
        # setting Raman Shift as index
        single_uploaded_data_file.set_index(RS, inplace=True)
        
        # saving data into dictionary
        all_uploaded_witek_data_files[uploaded_file.name[:-4]] = single_uploaded_data_file
        
        df = pd.concat([all_uploaded_witek_data_files[data_df] for data_df in all_uploaded_witek_data_files], axis=1)
    
    return df
