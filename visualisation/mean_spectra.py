import pandas as pd
import peakutils
import plotly.graph_objects as go
import streamlit as st

from processing import save_read
from processing import utils
from . import draw

MS = "Mean spectrum"
AV = "Average"
BS = "Baseline"
RS = "Raman Shift"
FLAT = "Flattened"
COR = "Corrected"
ORG = "Original spectrum"
RAW = "Raw Data"
OPT = "Optimised Data"
NORM = "Normalized"


def show_mean_plot(df, params):
    plots_color, template, display_opt, spectra_conversion_type = params
    file_name = 'mean'
    df2 = df.copy()
    
    # getting mean values for each raman shift
    df2[AV] = df2.mean(axis=1)
    df2 = df2.loc[:, [AV]]
    
    # Creating a Figure to add the mean spectrum in it
    fig_mean_corr = go.Figure()
    fig_mean_all = go.Figure()
    
    if spectra_conversion_type == RAW:
        file_name += '_raw'
        
        # Drawing plots of mean spectra of raw spectra
        fig_mean_corr = draw.add_traces_single_spectra(df2, fig_mean_corr, x=RS, y=AV,
                                                       name=f'{FLAT} + {AV} correction')
        
        fig_mean_corr = draw.fig_layout(template, fig_mean_corr, plots_colorscale=plots_color,
                                        descr='Raw mean spectra')
    
    elif spectra_conversion_type == OPT or spectra_conversion_type == NORM:
        file_name += '_optimized'
        
        if spectra_conversion_type == NORM:
            file_name += '_normalized'
            normalized_df2 = utils.normalize_spectra(df2, AV)
            df2 = pd.DataFrame(normalized_df2).dropna()
        
        # getting baseline for mean spectra
        deg, window = utils.adjust_spectras_window_n_degree()
        
        # Preparing data to plot
        df2[BS] = peakutils.baseline(df2.loc[:, AV], deg)
        df2 = utils.correct_baseline_single(df2, deg, MS)
        df2[FLAT] = df2['Corrected'].rolling(window=window).mean()
        df2.dropna(inplace=True)
        
        # Drowing figure of mean spectra after baseline correction and flattening
        # fig_mean_corr = go.Figure()
        fig_mean_corr = draw.add_traces_single_spectra(df2, fig_mean_corr, x=RS, y=FLAT,
                                                       name=f'{FLAT} + {BS} correction')
        fig_mean_corr = draw.fig_layout(template, fig_mean_corr, plots_colorscale=plots_color,
                                        descr='Mean spectra after baseline correction')
        
        # Drowing figure of mean spectra  + baseline
        # fig_mean_all = go.Figure()
        fig_mean_all = draw.add_traces(df2, fig_mean_all, x=RS, y=AV, name=AV)
        fig_mean_all = draw.add_traces(df2, fig_mean_all, x=RS, y=BS, name=BS)
        fig_mean_all = draw.add_traces(df2, fig_mean_all, x=RS, y=COR, name=COR)
        fig_mean_all = draw.add_traces(df2, fig_mean_all, x=RS, y=FLAT, name=f'{FLAT} + {BS} correction')
        draw.fig_layout(template, fig_mean_all, plots_colorscale=plots_color,
                        descr=f'{ORG}, {BS}, {COR}, and {COR}+ {FLAT}')
    
    st.write(fig_mean_corr)
    st.write(fig_mean_all)
    
    save_read.save_adj_spectra_to_file(df2, file_name)
