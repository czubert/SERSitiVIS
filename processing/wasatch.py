import pandas as pd
import streamlit as st

from constants import LABELS
from . import utils


def read_wasatch(uploaded_files, separator):
    temp_data_df = {}
    temp_meta_df = {}

    # Column to show
    col_to_show = LABELS["RAW_WASATCH"]

    spectra_params = {LABELS["CSV"]: {'sep': separator,
                                      # 'skiprows': lambda x: x < 34,
                                      'decimal': '.',
                                      'usecols': ['Pixel', 'Wavenumber', col_to_show],
                                      'skipinitialspace': True, },
                      LABELS["TXT"]: {'delim_whitespace': True, 'decimal': '.', 'skipinitialspace': True,
                                      'header': None},
                      }

    meta_params = {'sep': separator,
                   # 'skiprows': lambda x: x > 32,
                   'decimal': '.', 'index_col': 0,
                   'skipinitialspace': True, 'header': None}

    file_type = []

    for uploaded_file in uploaded_files:
        file_type.append(uploaded_file.name[-3:])

    if len(set(file_type)) > 1:
        st.warning(f'Update ONLY one type of data - either *.{LABELS["CSV"]} or *.{LABELS["TXT"]}')
        st.stop()
    
    for uploaded_file in uploaded_files:
        name = uploaded_file.name[:-(len(LABELS["PAT"]))]
        
        if uploaded_file.name[-3:] == LABELS["CSV"]:
            data, metadata = utils.read_spec(uploaded_file, spectra_params[LABELS["CSV"]], meta_params)
            data.set_index('Pixel', inplace=True)
            data.rename(columns={'Wavenumber': LABELS["RS"]}, inplace=True)
            
            data.dropna(inplace=True, how='any', axis=0)
            
            metadata = metadata.iloc[[18, 28, 30], :]
            
            data.rename(columns={col_to_show: f'{col_to_show} data: {name}'}, inplace=True)
            
            data.set_index('Raman Shift', inplace=True)
            
            temp_data_df[uploaded_file.name] = data
            temp_meta_df[uploaded_file.name] = metadata
        
        elif uploaded_file.name[-3:] == LABELS["TXT"]:
            data = utils.read_spec(uploaded_file, spectra_params[LABELS["TXT"]])
            
            data.dropna(inplace=True, how='any', axis=0)

            data = data.iloc[:, [2, 3, 4]]
            data.rename(columns={2: LABELS["RS"], 3: LABELS["PRCSD"], 4: LABELS["RAW_WASATCH"]}, inplace=True)

            data[LABELS["RS"]] = data[LABELS["RS"]].round(decimals=0)
            data.set_index(LABELS["RS"], inplace=True)
            data = pd.DataFrame(data[col_to_show])

            data.columns = [f'{name} - {col_to_show} data']
            temp_data_df[name] = data

    # TODO do we need it? is it a nice tool? if yes, we should do the same with bwtek,
    #  maybe we should use it in creating filenames
    # if file_type[0] == LABELS["CSV"]:
    #     if st.sidebar.button('Add metadata to plot name'):
    #         for key in temp_data_df:
    #             name = temp_data_df[key].columns[0]
    #             new_name = f'{name}_{temp_meta_df[key].loc[LABELS["IT"], 1]}ms_{temp_meta_df[key].loc[LABELS["LP"], 1]}%'
    #
    #             temp_data_df[key].rename(columns={name: new_name}, inplace=True)
    #
    data = pd.concat([temp_data_df[data_df] for data_df in temp_data_df], axis=1)

    return data
