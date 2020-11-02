import pandas as pd
import streamlit as st

from . import utils

RS = "Raman Shift"
DS = "Dark Subtracted #1"
RAW = 'Raw'
PRCSD = "Processed"
TXT = 'txt'
CSV = 'csv'


def read_wasatch(uploaded_files, separator):
    temp_data_df = {}
    temp_meta_df = {}

    # Column to show
    col_to_show = PRCSD

    col1, col2 = st.beta_columns(2)
    with col1:
        if st.button('Raw data'):
            col_to_show = RAW
    with col2:
        if st.button('Processed data'):
            col_to_show = PRCSD

    spectra_params = {CSV: {'sep': separator, 'skiprows': lambda x: x < 34 or x > 1058, 'decimal': '.',
                            'usecols': ['Pixel', 'Wavenumber', col_to_show],
                            'skipinitialspace': True, 'encoding': "utf-8"},
                      TXT: {'delim_whitespace': True, 'decimal': '.', 'skipinitialspace': True, 'encoding': 'utf-8',
                            'header': None},
                      }

    meta_params = {'sep': separator, 'skiprows': lambda x: x > 32, 'decimal': '.', 'index_col': 0,
                   'skipinitialspace': True, 'encoding': "utf-8", 'header': None}

    file_type = []

    for uploaded_file in uploaded_files:
        file_type.append(uploaded_file.name[-3:])

    if len(set(file_type)) > 1:
        st.warning(f'Update ONLY one type of data - either *.{CSV} or *.{TXT}')
        st.stop()

    for uploaded_file in uploaded_files:

        if uploaded_file.name[-3:] == CSV:
            data, metadata = utils.read_spec(uploaded_file, spectra_params[CSV], meta_params)
            data.set_index('Pixel', inplace=True)
            data.rename(columns={'Wavenumber': RS}, inplace=True)

            data.dropna(inplace=True, how='any', axis=0)

            data.rename(columns={col_to_show: uploaded_file.name[:-4]}, inplace=True)

            data.set_index('Raman Shift', inplace=True)

            temp_data_df[uploaded_file.name] = data
            temp_meta_df[uploaded_file.name] = metadata

        elif uploaded_file.name[-3:] == TXT:
            data = utils.read_spec(uploaded_file, spectra_params[TXT])

            name = uploaded_file.name[:-4]

            data.dropna(inplace=True, how='any', axis=0)

            data = data.iloc[:, [2, 3, 4]]
            data.rename(columns={2: RS, 3: PRCSD, 4: RAW}, inplace=True)

            data[RS] = data[RS].round(decimals=0)
            data.set_index(RS, inplace=True)
            data = pd.DataFrame(data[col_to_show])

            data.columns = [f'{col_to_show}: {name}']
            temp_data_df[uploaded_file.name[:-4]] = data

    return temp_data_df, temp_meta_df
