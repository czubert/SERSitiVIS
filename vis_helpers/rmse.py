import streamlit as st

import processing
from constants import LABELS
from . import sidebar
from . import rmse_utils


# TODO rmse można chyba po prostu wrzucić gdzieś przy wizualizacji, albo tu i przy wizualizacji
# TODO do liczenia RMSE trzeba użyć widm po korekcji baselinu i po normalizacji żeby były wiarygodne
# TODO dodać możliwość wyboru peaku (okolic peaku i wybrać maxa)
# TODO użyć metody findpeaks to znajdowania pików (i może przekazać listę do widgetu,
# z któego klient ma wybrać)
# TODO sprawdzić jak liczą w publikacjach RMSE, czy to chodzi o różnice intensywnosci miedzy widmami,
# czy o stosunek pików, który w sumie powinien być stały... więc trochę bez sensu

def main():
    spectra_types = ['EMPTY', 'BWTEK', 'RENI', 'WITEC', 'WASATCH', 'TELEDYNE', 'JOBIN']
    spectrometer = st.sidebar.selectbox("Choose spectra type",
                                        spectra_types,
                                        format_func=LABELS.get,
                                        index=0
                                        )
    sidebar.print_widgets_separator()
    
    files = st.sidebar.file_uploader(label='Upload your data or try with ours',
                                     accept_multiple_files=True,
                                     type=['txt', 'csv'])
    
    if files:
        df = processing.save_read.files_to_df(files, spectrometer)
        # st.write(df)
        
        # Calling the function with parameters
        peak1 = df.loc[680:725, :]  # TODO to wziąć z peakfindera
        peak2 = df.loc[990:1010, :]  # TODO to wziąć z peakfindera
        bg = df.loc[938:941, :]  # TODO to wziąćz baseline'a
        
        rmse_utils.rsd(peak1, peak2, bg)
