import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from constants import LABELS
from processing import save_read
from processing import utils
from . import draw


def show_grouped_plot(df, plots_color, template, spectra_conversion_type, shift, vals):
    file_name = 'grouped'
    fig = go.Figure()
    df = df.copy()

    if spectra_conversion_type == LABELS["RAW"]:
        file_name += '_raw'

        for col_ind, col in enumerate(df.columns):
            df[col] = df[col] + shift * col_ind

        fig = px.line(df, x=df.index, y=df.columns, color_discrete_sequence=plots_color)

    elif spectra_conversion_type in {LABELS["OPT"], LABELS["NORM"]}:
        if spectra_conversion_type == LABELS["NORM"]:
            file_name += '_normalized'
        else:
            file_name += '_optimized'

        for col_ind, col in enumerate(df.columns):
            corrected = df[col]
        
            if spectra_conversion_type == 'Normalized':
                corrected = utils.normalize_spectrum(df, None)
                # corrected = pd.DataFrame(corrected)#.dropna()

            corrected = corrected.rolling(window=vals[col][1]).mean()
            # corrected = utils.smoothen_the_spectra(corrected, window=vals[col][1])

            ### TODO TERAZ TU POGRZEBAĆ
            corrected = utils.subtract_baseline(corrected, vals[col][0])#.dropna()
        
            df[col] = corrected.iloc[col_ind]
        
            if col_ind != 0:
                corrected.iloc[:, 0] += shift * col_ind

            fig = draw.add_traces(corrected.reset_index(), fig, x=LABELS["RS"], y=col, name=col)

    fig.update_traces(line=dict(width=3.5))
    draw.fig_layout(template, fig, plots_colorscale=plots_color, descr=LABELS["OPT_S"])
    save_read.save_adj_spectra_to_file(df, file_name)
    return fig


