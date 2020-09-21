import plotly.express as px
import plotly.graph_objects as go

import streamlit as st
import pandas as pd

RS = 'Raman Shift'
DS = 'Dark Subtracted #1'

def draw_plot(template, df_for_plot, descr='Chosen spectra', y_value='Custom'):
    """
    # dictionary of tuples of dfs separated corresponding to the type of substrate
    :param df_for_plot: DataFrame
    :param descr: String
    :param y_value: String
    :return: Plotly object - Figure
    """


    if y_value == 'Custom' or y_value == 'all':
        fig = px.line(df_for_plot, x=RS, y=DS, width=950, height=650,
                      # color_discrete_sequence=px.colors.qualitative.Alphabet, error_y='Average_err')
                      color_discrete_sequence=px.colors.qualitative.Alphabet)

    elif y_value == 'Mean spectrum':
        fig = px.line(df_for_plot, y="Average", width=950, height=650,
                      # color_discrete_sequence=px.colors.qualitative.Alphabet, error_y='Average_err')
                      color_discrete_sequence=px.colors.qualitative.Alphabet)

    elif y_value == 'Grouped spectra':
        df_for_plot.reset_index(inplace=True)
        corrected_df = pd.melt(df_for_plot, id_vars=df_for_plot.columns[0], value_vars=df_for_plot.columns[1:])
        fig = px.line(corrected_df, x=RS, y='value', color='variable', width=950, height=650,
                      color_discrete_sequence=px.colors.qualitative.Alphabet)

    # changing layout and styles
    fig.update_layout(title=descr, template=template, height=450,
                      xaxis_title=f"{RS} [cm^-1]",
                      yaxis_title="Intensity",
                      title_font_size=20,
                      legend=go.layout.Legend(x=0.5, y=-0.2, traceorder="normal",
                                              font=dict(
                                                  family="sans-serif",
                                                  size=10,
                                                  color="black"
                                              ),
                                              bgcolor="#fff",
                                              bordercolor="#ccc",
                                              borderwidth=0.4,
                                              orientation='h',
                                              xanchor='auto',
                                              itemclick='toggle',

                                              ))

    return fig


def fig_layout(template, fig, descr='Chosen spectra'):
    # changing layout and styles
    fig.update_layout(title=descr, template=template, height=450,
                      xaxis_title=f"{RS} [cm^-1]",
                      yaxis_title="Intensity",
                      title_font_size=20,
                      width=950,
                      legend=go.layout.Legend(x=0.5, y=-0.2, traceorder="normal",
                                              font=dict(
                                                  family="sans-serif",
                                                  size=10,
                                                  color="black"
                                              ),
                                              bgcolor="#fff",
                                              bordercolor="#ccc",
                                              borderwidth=0.4,
                                              orientation='h',
                                              xanchor='auto',
                                              itemclick='toggle',

                                              ))

    return fig
