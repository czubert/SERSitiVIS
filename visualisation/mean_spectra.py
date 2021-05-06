import pandas as pd
import peakutils
import plotly.graph_objects as go
import streamlit as st

from constants import LABELS
from processing import save_read
from processing import utils
from . import draw


def show_mean_plot(df, plots_color, template, spectra_conversion_type):
    file_name = 'mean'
    df = df.copy()
    col1, col2 = st.beta_columns((2, 1))
    
    # getting mean values for each raman shift
    df[LABELS["AV"]] = df.mean(axis=1)
    df = df.loc[:, [LABELS["AV"]]]
    
    # Creating a Figure to add the mean spectrum in it
    fig_mean_corr = go.Figure()
    fig_mean_all = go.Figure()
    
    if spectra_conversion_type == LABELS["RAW"]:
        file_name += '_raw'
        
        # Drawing plots of mean spectra of raw spectra
        fig_mean_corr = draw.add_traces_single_spectra(df, fig_mean_corr, x=LABELS["RS"], y=LABELS["AV"],
                                                       name=f'{LABELS["FLAT"]} + {LABELS["AV"]} correction')
        
        fig_mean_corr = draw.fig_layout(template, fig_mean_corr, plots_colorscale=plots_color,
                                        descr='Raw mean spectra')
    
    elif spectra_conversion_type == LABELS["OPT"] or spectra_conversion_type == LABELS["NORM"]:
        file_name += '_optimized'
        
        if spectra_conversion_type == LABELS["NORM"]:
            file_name += '_normalized'
            normalized_df2 = utils.normalize_spectrum(df, LABELS["AV"])
            df = pd.DataFrame(normalized_df2).dropna()
        
        with col2:
            st.markdown('## Adjust your spectra')
            st.header('\n\n\n\n')
            
            st.header('\n\n\n\n')
            st.header('\n\n\n\n')
            st.header('\n\n\n\n')
            
            deg = utils.choosing_regression_degree(name=file_name)
            window = utils.choosing_smoothening_window(name=file_name)
        
        # getting baseline for mean spectra
        df[LABELS["BS"]] = peakutils.baseline(df.loc[:, LABELS["AV"]], deg)
        df = utils.subtract_baseline(df, deg, key=LABELS["MS"], model=LABELS["AV"])
        st.write(df)
        
        # smoothing spectra with rolling method
        df = utils.smoothen_the_spectra(df, window=window, key=LABELS["MS"])
        df.dropna(inplace=True)
        
        # Drowing figure of mean spectra after baseline correction and flattening
        fig_mean_corr = draw.add_traces_single_spectra(df, fig_mean_corr, x=LABELS["RS"], y=LABELS["FLAT"],
                                                       name=f'{LABELS["FLAT"]} + {LABELS["BS"]} correction')
        fig_mean_corr = draw.fig_layout(template, fig_mean_corr, plots_colorscale=plots_color,
                                        descr='Mean spectra after baseline correction')
        
        # Drowing figure of mean spectra  + baseline
        fig_mean_all = draw.add_traces(df, fig_mean_all, x=LABELS["RS"], y=LABELS["AV"], name=LABELS["AV"])
        fig_mean_all = draw.add_traces(df, fig_mean_all, x=LABELS["RS"], y=LABELS["BS"], name=LABELS["BS"])
        fig_mean_all = draw.add_traces(df, fig_mean_all, x=LABELS["RS"], y=LABELS["COR"], name=LABELS["COR"])
        fig_mean_all = draw.add_traces(df, fig_mean_all, x=LABELS["RS"], y=LABELS["FLAT"],
                                       name=f'{LABELS["FLAT"]} + {LABELS["BS"]} correction')
        
        draw.fig_layout(template, fig_mean_all, plots_colorscale=plots_color,
                        descr=f'{LABELS["ORG"]}, {LABELS["BS"]}, {LABELS["COR"]}, and {LABELS["COR"]}+ {LABELS["FLAT"]}')
    with col1:
        if spectra_conversion_type == LABELS["RAW"]:
            st.write(fig_mean_corr)
        else:
            st.write(fig_mean_corr)
            st.write(fig_mean_all)
    
    save_read.save_adj_spectra_to_file(df, file_name)
