import pandas as pd
import peakutils
import plotly.graph_objects as go
import plotly.express as px

from constants import LABELS
from processing import save_read
from processing import utils
from . import draw


def show_mean_plot(df, plots_color, template, spectra_conversion_type, deg, window):
    file_name = 'mean'
    df = df.copy()

    # getting mean values for each raman shift
    df[LABELS["AV"]] = df.mean(axis=1)
    df = df.loc[:, [LABELS["AV"]]]
    
    # Creating a Figure to add the mean spectrum in it
    fig_mean_corr = go.Figure()
    fig_mean_all = go.Figure()
    
    if spectra_conversion_type == LABELS["RAW"]:
        file_name += '_raw'
        
        # Drawing plots of mean spectra of raw spectra
        fig_mean_corr = px.line(df, x=df.index, y=[LABELS["AV"]],
                                labels=[f'{LABELS["FLAT"]} + {LABELS["AV"]} correction'],
                                color_discrete_sequence=plots_color,
                                )

        fig_mean_corr = draw.fig_layout(template, fig_mean_corr, plots_colorscale=None,
                                        descr='Mean spectrum')
    
    elif spectra_conversion_type == LABELS["OPT"] or spectra_conversion_type == LABELS["NORM"]:
        file_name += '_optimized'

        if spectra_conversion_type == LABELS["NORM"]:
            file_name += '_normalized'
            normalized_df2 = utils.normalize_spectrum(df, LABELS["AV"])
            df = pd.DataFrame(normalized_df2)

        # getting baseline for mean spectra
        df[LABELS["BS"]] = peakutils.baseline(df.loc[:, LABELS["AV"]], deg)
        df = utils.subtract_baseline(df, deg, key=LABELS["MS"], model=LABELS["AV"])

        # smoothing spectra with rolling method
        df = utils.smoothen_the_spectra(df, window=window, key=LABELS["MS"])
        df.dropna(inplace=True)

        # Drawing figure of mean spectra after baseline correction and flattening
        fig_mean_corr = px.line(df, x=df.index, y=[LABELS["FLAT"]],
                                color_discrete_sequence=plots_color,
                                )
        fig_mean_corr = draw.fig_layout(template, fig_mean_corr, plots_colorscale=None,
                                        descr='Mean spectrum after baseline correction')
        fig_mean_corr.update_traces(hovertemplate=None)
        fig_mean_corr.update_layout(hovermode="x")

        fig_mean_all = px.line(df, x=df.index, y=[LABELS["AV"], LABELS["BS"], LABELS["COR"], LABELS["FLAT"]],
                               color_discrete_sequence=plots_color)
        fig_mean_all = draw.fig_layout(template, fig_mean_all, plots_colorscale=plots_color,
                                       descr='Mean spectra after baseline correction')

    save_read.save_adj_spectra_to_file(df, file_name)

    if spectra_conversion_type == LABELS["RAW"]:
        return fig_mean_corr,
    else:
        return fig_mean_corr, fig_mean_all
