import plotly.express as px
import plotly.graph_objects as go

import streamlit as st
import pandas as pd

RS = 'Raman Shift'
DS = 'Dark Subtracted #1'

def draw_plot(df_for_plot, descr='Chosen spectra', y_value='Custom'):
    """
    # dictionary of tuples of dfs separated corresponding to the type of substrate
    :param df_for_plot: DataFrame
    :param descr: String
    :param y_value: String
    :return: Plotly object - Figure
    """


    if y_value == 'Custom' or y_value == 'all':
        fig = px.line(df_for_plot, x=RS, y=DS,
                      color_discrete_sequence=px.colors.qualitative.Alphabet)
        return fig
