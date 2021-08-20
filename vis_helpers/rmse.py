import streamlit as st
import pandas as pd
import sklearn.preprocessing
from scipy.signal import find_peaks

import processing
from constants import LABELS
from . import sidebar
from . import rmse_utils


# TODO rmse można chyba po prostu wrzucić gdzieś przy wizualizacji, albo tu i przy wizualizacji
# TODO do liczenia RMSE trzeba użyć widm po korekcji baselinu i po normalizacji żeby były wiarygodne !!!
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

        rescale = st.sidebar.checkbox("Rescale")
        if rescale:
            scaler = sklearn.preprocessing.MinMaxScaler()
            rescaled_data = scaler.fit_transform(df)
            df = pd.DataFrame(rescaled_data, columns=df.columns, index=df.index)

        # Calling the function with parameters
        peak1 = df.loc[680:725, :]  # TODO to wziąć z peakfindera
        peak2 = df.loc[990:1010, :]  # TODO to wziąć z peakfindera
        bg = df.loc[938:941, :]  # TODO to wziąćz baseline'a
        rmse_utils.rsd(peak1, peak2, bg)

        from scipy.signal import find_peaks
        import numpy as np

        df3 = pd.DataFrame()

        for col in df.columns:
            # TODO dodać opcję wyświetlania peaków na wykresach z podpisami od pasm dla maximow lokalnych
            # oczywiście gdzieś w wersji wizualizacyjnej
            peaks = np.array(find_peaks(df[col], width=15, distance=5, rel_height=20, height=3000))[0]

            df3 = pd.concat([df3, df[col].reset_index().iloc[pd.Series(peaks), :].set_index('Raman Shift')], axis=1)

        # TODO dupa jest, bo znajduje piki z malymi przesunieciami przez co wskakują nany ;/
        # trzebaby chyba nie likwidowac nanów, tylko brać max wartość z przediału Raman Shfita
        # zblizonego do kazdego peaku, przez co będziemy prównywali peaki przesunięte o +-1 cm^-1
        # (to niby mi sie troche udalo zrobic, ale dalej nie wiem co tam sie pierdoli ze w dwoch miejsach sa
        # te same wartosci, tak jakbym mial dwa rowne peaki

        # FIX poniżej moje wypociny mające na celu splaszczenie ramanshifta i przypisanie splaszczonym
        #  ramanshiftom srednich wartości, ale coś poszło nie do końca tak jak chciałem ; /

        # df po zestawieniu peaków używając findpeaks
        st.write(df3)

        df3.reset_index(inplace=True)
        for col in df3.columns:
            df3[col] = df3[col].rolling(window=2, min_periods=1, center=True).max()
        # df3 = df3.interpolate(axis=1).bfill().ffill()
        df3 = df3.set_index('Raman Shift')

        # df po rollingu i interpolacji, zeby splaszczyc roznice w ramanshiftach
        st.write(df3)

        import plotly.express as px
        fig = px.scatter(df3.dropna())
        st.plotly_chart(fig, use_container_width=True)
        fig = px.line(df)
        st.plotly_chart(fig, use_container_width=True)
