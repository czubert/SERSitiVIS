import pandas as pd
import streamlit as st

from . import utils

RS = "Raman Shift"
DS = "Dark Subtracted #1"
RAW = 'Raw'
PRCSD = "Processed"
TXT = 'txt'
CSV = 'csv'
IT = 'Integration Time'
LP = 'Laser Power'
PAT = '-20201009-093705-137238-WP-00702.txt'


def read_wasatch(uploaded_files, separator):
    temp_data_df = {}
    temp_meta_df = {}

    # Column to show
    col_to_show = RAW
    st.sidebar.markdown(f"<p style='color:red'>----------------------------------------------</p>",
                        unsafe_allow_html=True)

    modified_data = st.sidebar.radio(
        "Choose type of data",
        (RAW, PRCSD), index=0)

    if modified_data == RAW:
        col_to_show = RAW
    elif modified_data == PRCSD:
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
        name = uploaded_file.name[:-(len(PAT))]

        if uploaded_file.name[-3:] == CSV:
            data, metadata = utils.read_spec(uploaded_file, spectra_params[CSV], meta_params)
            data.set_index('Pixel', inplace=True)
            data.rename(columns={'Wavenumber': RS}, inplace=True)

            data.dropna(inplace=True, how='any', axis=0)

            metadata = metadata.iloc[[18, 28, 30], :]

            data.rename(columns={col_to_show: f'{col_to_show} data: {name}'}, inplace=True)

            data.set_index('Raman Shift', inplace=True)

            temp_data_df[uploaded_file.name] = data
            temp_meta_df[uploaded_file.name] = metadata

        elif uploaded_file.name[-3:] == TXT:
            data = utils.read_spec(uploaded_file, spectra_params[TXT])

            data.dropna(inplace=True, how='any', axis=0)

            data = data.iloc[:, [2, 3, 4]]
            data.rename(columns={2: RS, 3: PRCSD, 4: RAW}, inplace=True)

            data[RS] = data[RS].round(decimals=0)
            data.set_index(RS, inplace=True)
            data = pd.DataFrame(data[col_to_show])

            data.columns = [f'{name} - {col_to_show} data']
            temp_data_df[name] = data

    if file_type[0] == CSV:
        if st.sidebar.button('Add metadata to plot name'):
            for key in temp_data_df:
                name = temp_data_df[key].columns[0]
                new_name = f'{name}_{temp_meta_df[key].loc[IT, 1]}ms_{temp_meta_df[key].loc[LP, 1]}%'

                temp_data_df[key].rename(columns={name: new_name}, inplace=True)

    data = pd.concat([temp_data_df[data_df] for data_df in temp_data_df], axis=1)

    return data
