import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from constants import LABELS
from processing import save_read
from processing import utils
from . import draw


def show_grouped_plot(df, plots_color, template, spectra_conversion_type, shift):
    file_name = 'grouped'
    fig = go.Figure()
    col1, col2 = st.beta_columns((2, 1))
    df = df.copy()

    if spectra_conversion_type == LABELS["RAW"]:
        file_name += '_raw'

        for col_ind, col_name in enumerate(df.columns):
            df[col_name] = df[col_name] + shift * col_ind

        fig = px.line(df, x=df.index, y=df.columns)
        fig.update_traces(line=dict(width=3.5))
        draw.fig_layout(template, fig, plots_colorscale=plots_color, descr=LABELS["ORG"])
        save_read.save_adj_spectra_to_file(df, file_name)

    elif spectra_conversion_type == LABELS["OPT"] or spectra_conversion_type == LABELS["NORM"]:
        file_name += '_optimized'
        df_to_save = pd.DataFrame()
    
        if spectra_conversion_type == LABELS["NORM"]:
            file_name += '_normalized'
    
        adjust_plots_globally = st.radio(
            "Adjust all spectra or each spectrum?",
            ('all', 'each'), index=0)
        with col2:
            st.markdown('## Adjust your spectra')
        
            if adjust_plots_globally == 'all':
                deg = utils.choosing_regression_degree()
                window = utils.choosing_smoothening_window()
                vals = {col: (deg, window) for col in df.columns}
        
            elif adjust_plots_globally == 'each':
                with st.beta_expander("Customize your chart"):
                    vals = {col: (utils.choosing_regression_degree(col), utils.choosing_smoothening_window(col)) for col
                            in df.columns}
    
        for col_ind, col in enumerate(df.columns):
        
            corrected = pd.DataFrame(df.loc[:, col]).dropna()
        
            if spectra_conversion_type == 'Normalized':
                normalized_df = utils.normalize_spectrum(df, col)
                corrected = pd.DataFrame(normalized_df).dropna()
        
            corrected = utils.smoothen_the_spectra(corrected, window=vals[col][1])
            corrected = utils.subtract_baseline(corrected, vals[col][0]).dropna()
        
            df_to_save[col] = corrected.iloc[col_ind]
        
            if col_ind != 0:
                corrected.iloc[:, 0] += shift * col_ind

            fig = draw.add_traces(corrected.reset_index(), fig, x=LABELS["RS"], y=col,
                                               name=col)
            draw.fig_layout(template, fig, plots_colorscale=plots_color, descr=LABELS["OPT_S"])
        save_read.save_adj_spectra_to_file(df_to_save, file_name)
    with col1:
        st.write(fig)



