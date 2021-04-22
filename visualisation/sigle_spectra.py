import pandas as pd
import peakutils
import plotly.graph_objects as go
import streamlit as st

from processing import save_read
from processing import utils
from . import draw

SINGLE = 'Single spectra'
MS = "Mean spectrum"
GS = "Grouped spectra"
P3D = "Plot 3D"

AV = "Average"
BS = "Baseline"
RS = "Raman Shift"
DS = "Dark Subtracted #1"
DEG = "Polynominal degree"
WINDOW = "Set window for spectra flattening"
DFS = {'ML model grouped spectra': f'{DS}', 'ML model mean spectra': f'{AV}'}
FLAT = "Flattened"
COR = "Corrected"
ORG = "Original spectrum"
RAW = "Raw Data"
OPT = "Optimised Data"
NORM = "Normalized"
OPT_S = "Optimised Spectrum"


def show_single_plots(df, params):
    plots_color, template, display_opt, spectra_conversion_type = params
    global df_visual, plot_line, description, fig_single_all
    df2 = df.copy()
    
    for col in range(len(df2.columns)):
        st.write('=======================================================================================')
        # Creating DataFrame that will be shown on plot
        spectra_to_show = pd.DataFrame(df2.iloc[:, col]).dropna()
        
        # TODO What might be useful - would be a function to choose which part of the spectrum should be
        # TODO used for the baseline fitting.
        # Adding column with baseline that will be show on plot
        
        # Showing spectra after baseline correction
        fig_single_corr = go.Figure()
        
        if spectra_conversion_type == RAW:
            df_visual = spectra_to_show
            plot_line = df_visual.columns[0]
            description = ORG
        
        elif spectra_conversion_type == OPT or spectra_conversion_type == NORM:
            if spectra_conversion_type == NORM:
                normalized_df2 = utils.normalize_spectra(df2, col)
                
                spectra_to_show = pd.DataFrame(normalized_df2).dropna()
            
            plot_line = FLAT
            description = OPT_S
            
            col1, col2 = st.beta_columns(2)
            with col1:
                deg = st.slider(f'{DEG} plot nr: {col}', min_value=0, max_value=20, value=5, key=f'{col}')
            with col2:
                window = st.slider(f'{WINDOW} plot nr: {col}', min_value=1, max_value=20, value=3, key=f'{col}')
            
            spectra_to_show[BS] = peakutils.baseline(spectra_to_show[spectra_to_show.columns[0]], deg)
            
            # Creating DataFrame with applied Baseline correction
            corrected_df = utils.correct_baseline_single(spectra_to_show, deg, spectra_to_show.columns[0])
            # Refining DataFrame to make spectra flattened
            corrected_df[FLAT] = corrected_df[COR].rolling(window=window).mean()
            corrected_df.dropna(inplace=True)
            
            df_visual = corrected_df
            
            # Showing spectra before baseline correction + baseline function
            fig_single_all = go.Figure()
            draw.fig_layout(template, fig_single_all, plots_colorscale=plots_color,
                            descr=f'{ORG}, {BS}, and {FLAT} + {BS}')
            
            specs = {'org': df_visual.columns[0], BS: BS, COR: COR, FLAT: FLAT}
            
            for spec in specs.keys():
                if spec == FLAT:
                    name = f'{FLAT} + {BS} correction'
                else:
                    name = specs[spec]
                
                fig_single_all = draw.add_traces(df_visual, fig_single_all,
                                                 x=RS, y=specs[spec], name=name)
        
        fig_single_corr = draw.add_traces_single_spectra(df_visual, fig_single_corr, x=RS, y=plot_line,
                                                         name=df_visual.columns[0])
        
        draw.fig_layout(template, fig_single_corr, plots_colorscale=plots_color, descr=description)
        
        if spectra_conversion_type == RAW:
            st.write(fig_single_corr)
        else:
            st.write(fig_single_corr)
            st.write(fig_single_all)
        
        file_name = f'{df_visual.columns[0]}_{FLAT}_{BS}_correction'
        
        save_read.save_adj_spectra_to_file(df_visual, file_name, key=f'{col}')
