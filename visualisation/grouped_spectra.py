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
SHIFT = 'Shift spectra from each other'


def show_grouped_plot(df, plots_color, template, spectra_conversion_type):
    global shift, col1
    file_name = 'grouped'
    df_to_save = pd.DataFrame()

    st.write('========================================================================')
    
    fig_grouped_corr = go.Figure()
    
    if spectra_conversion_type == RAW:
        file_name += '_raw'
        shift = st.slider(SHIFT, 0, 30000, 0, 250)
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

        if spectra_conversion_type == OPT:
            shift = st.slider(SHIFT, 0, 30000, 0, 250)

        elif spectra_conversion_type == NORM:
            file_name += '_normalized'
            shift = st.slider(SHIFT, 0.0, 1.0, 0.0, 0.1)

        adjust_plots_globally = st.radio(
            "Adjust all spectra or each spectrum?",
            ('all', 'each'), index=0)
        col1, col2 = st.beta_columns((2, 1))
        with col2:
            st.markdown('## Adjust your spectra')
    
            if adjust_plots_globally == 'all':
                deg, window = utils.degree_and_window_sliders()
                vals = {col: (deg, window) for col in df.columns}
    
            elif adjust_plots_globally == 'each':
                with st.beta_expander("Customize your chart"):
                    vals = {col: utils.degree_and_window_sliders(col) for col in df.columns}

        for col_ind, col in enumerate(df.columns):
            corrected = utils.process_grouped_opt_spec(df=df,
                                                       spectra_conversion_type=spectra_conversion_type,
                                                       col=col,
                                                       deg=vals[col][0],
                                                       window=vals[col][1])
            df_to_save[col] = corrected.iloc[col_ind]
    
            if col_ind != 0:
                corrected.iloc[:, 0] += shift * col_ind
    
            fig_grouped_corr = draw.add_traces(corrected.reset_index(), fig_grouped_corr, x=RS, y=col,
                                               name=col)
            draw.fig_layout(template, fig_grouped_corr, plots_colorscale=plots_color, descr=OPT_S)
    with col1:
        st.write(fig_grouped_corr)

    save_read.save_adj_spectra_to_file(df_to_save, file_name)
