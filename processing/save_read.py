import streamlit as st


# TODO does this function has any occurance in the code beside this one?
def save_adj_spectra_to_file(df_to_save, file_name, key='default'):
    """
    Save data directly from streamlit as csv file after pressing 'download' button.
    :param df_to_save: DataFrame
    :param file_name: String
    :param key: String
    """
    from processing.utils import download_button
    # User can set custom name for a file to write
    input_file_name = st.text_input(
        'Enter the name of the file to save (if not given it will be added automatically based on the name of the file)',
        key=key)
    
    # Checks if user have set a file name if not, it will be default
    if input_file_name:
        file_name = input_file_name
    else:
        file_name += '_SERSitiVIS_spectra'
    
    tmp_download_link = download_button(df_to_save.reset_index(), f'{file_name}.csv',
                                        button_text='Click here to download your text!')
    
    st.markdown(tmp_download_link, unsafe_allow_html=True)
