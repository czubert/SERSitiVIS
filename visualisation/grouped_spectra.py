import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from processing import save_read
from processing import utils
from . import draw

GS = "Grouped spectra"
RS = "Raman Shift"
ORG = "Original spectrum"
RAW = "Raw Data"
OPT = "Optimised Data"
NORM = "Normalized"
OPT_S = "Optimised Spectrum"


def show_grouped_plot(df, plots_color, template, spectra_conversion_type, shift):
    global col1
    file_name = 'grouped'
    df_to_save = pd.DataFrame()
    
    st.write('========================================================================')
    
    fig_grouped_corr = go.Figure()
    
    if spectra_conversion_type == RAW:
        file_name += '_raw'
        
        col1, col2 = st.beta_columns((2))
        for col in range(len(df.columns)):
            col_name = df.columns[col]
            
            corrected = pd.DataFrame(df.loc[:, col_name]).dropna()
            
            df_to_save[col_name] = corrected[col_name]
            
            if col != 0:
                corrected.iloc[:, 0] += shift * col
            
            fig_grouped_corr = draw.add_traces(corrected.reset_index(), fig_grouped_corr, x=RS, y=col_name,
                                               name=f'{df.columns[col]}')
        draw.fig_layout(template, fig_grouped_corr, plots_colorscale=plots_color, descr=ORG)
    
    
    
    elif spectra_conversion_type == OPT or spectra_conversion_type == NORM:
        file_name += '_optimized'
        df = df.copy()
        df_to_save = pd.DataFrame()
    
        if spectra_conversion_type == NORM:
            file_name += '_normalized'
    
        adjust_plots_globally = st.radio(
            "Adjust all spectra or each spectrum?",
            ('all', 'each'), index=0)
        col1, col2 = st.beta_columns((2, 1))
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
        
            fig_grouped_corr = draw.add_traces(corrected.reset_index(), fig_grouped_corr, x=RS, y=col,
                                               name=col)
            draw.fig_layout(template, fig_grouped_corr, plots_colorscale=plots_color, descr=OPT_S)
    with col1:
        st.write(fig_grouped_corr)
    
    save_read.save_adj_spectra_to_file(df_to_save, file_name)
