import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.signal import find_peaks
from sklearn.preprocessing import MinMaxScaler

import processing
from constants import LABELS
from . import rmse_utils
from . import sidebar

SLIDERS_PARAMS_RAW = {'rel_height': dict(min_value=1, max_value=100, value=20, step=1),
                      'height': dict(min_value=1000, max_value=100000, value=10000, step=1000),
                      }
SLIDERS_PARAMS_NORMALIZED = {'rel_height': dict(min_value=0.01, max_value=1., value=0.5, step=0.01),
                             'height': dict(min_value=0.001, max_value=1., value=0.1, step=0.001),
                             }


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
        df = df.interpolate().bfill().ffill()

        plot_x_min = int(df.index.min())
        plot_x_max = int(df.index.max())

        rescale = st.sidebar.checkbox("Rescale")
        if rescale:
            scaler = MinMaxScaler()
            rescaled_data = scaler.fit_transform(df)
            df = pd.DataFrame(rescaled_data, columns=df.columns, index=df.index)
            sliders_params = SLIDERS_PARAMS_NORMALIZED
        else:
            sliders_params = SLIDERS_PARAMS_RAW

        peak1_range = st.slider('Peak 1 range', min_value=plot_x_min, max_value=plot_x_max, value=[plot_x_min, plot_x_max])
        peak2_range = st.slider('Peak 2 range', min_value=plot_x_min, max_value=plot_x_max, value=[plot_x_min, plot_x_max])
        bg_range = st.slider('Backgroung range', min_value=plot_x_min, max_value=plot_x_max, value=[plot_x_min, plot_x_max])
        peak1_range = [int(i) for i in peak1_range.split('__')]
        peak2_range = [int(i) for i in peak2_range.split('__')]
        bg_range = [int(i) for i in bg_range.split('__')]

        fig = px.line(df)
        fig.update_xaxes(range=[plot_x_min, plot_x_max])
        for ran, text in zip([peak1_range, peak2_range, bg_range], ['Peak 1', 'Peak 2', 'background']):
            fig.add_vline(x=ran[0], line_dash="dash", annotation_text=text)
            fig.add_vline(x=ran[1], line_dash="dash")

        st.plotly_chart(fig, use_container_width=True)

        peak1 = df.loc[peak1_range[0]:peak1_range[1], :]
        peak2 = df.loc[peak2_range[0]:peak2_range[1], :]
        bg = df.loc[bg_range[0]:bg_range[1], :]  # TODO to wziąć z baseline'a

        rmse_utils.rsd(peak1, peak2, bg)

        cols = st.beta_columns(4)
        peak_width = cols[0].slider('Min width', min_value=5, max_value=100, value=15, step=5, )
        peak_distance = cols[1].slider('Min distance', min_value=1, max_value=100, value=5, step=1, )
        peak_rel_height = cols[2].slider('Min relative height', **sliders_params['rel_height'])
        peak_height = cols[3].slider('Min absolute height', **sliders_params['height'])

        peak_width = int(peak_width)
        peak_distance = int(peak_distance)
        peak_rel_height = float(peak_rel_height) if rescale else int(peak_rel_height)
        peak_height = float(peak_height) if rescale else int(peak_height)

        peak_df = pd.DataFrame()
        for col in df.columns:
            # TODO dodać opcję wyświetlania peaków na wykresach z podpisami od pasm dla maximow lokalnych
            # oczywiście gdzieś w wersji wizualizacyjnej
            peaks = np.array(find_peaks(df[col], width=peak_width, distance=peak_distance,
                                        rel_height=peak_rel_height, height=peak_height)
                             )[0]
            peak_df = pd.concat([peak_df, df[col].reset_index().iloc[pd.Series(peaks), :].set_index('Raman Shift')],
                                axis=1)

        # TODO dupa jest, bo znajduje piki z malymi przesunieciami przez co wskakują nany ;/
        # trzebaby chyba nie likwidowac nanów, tylko brać max wartość z przediału Raman Shfita
        # zblizonego do kazdego peaku, przez co będziemy prównywali peaki przesunięte o +-1 cm^-1
        # (to niby mi sie troche udalo zrobic, ale dalej nie wiem co tam sie pierdoli ze w dwoch miejsach sa
        # te same wartosci, tak jakbym mial dwa rowne peaki

        # FIX poniżej moje wypociny mające na celu splaszczenie ramanshifta i przypisanie splaszczonym
        #  ramanshiftom srednich wartości, ale coś poszło nie do końca tak jak chciałem ; /


        fig = px.scatter(peak_df, x=peak_df.index, y=peak_df.columns, title='Peak positions')
        fig.update_xaxes(range=[plot_x_min, plot_x_max])
        st.plotly_chart(fig, use_container_width=True)

