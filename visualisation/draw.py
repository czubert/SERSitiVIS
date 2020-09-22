import plotly.express as px
import plotly.graph_objects as go

import streamlit as st

RS = 'Raman Shift'
DS = 'Dark Subtracted #1'


def fig_layout(template, fig, descr='Chosen spectra'):
    """
    Changing layout and styles
    :param template: Str, Plotly template
    :param fig: plotly.graph_objs._figure.Figure
    :param descr: Str
    :return: plotly.graph_objs._figure.Figure
    """

    fig.update_layout(title=descr,
                      showlegend=True,
                      template=template,
                      title_font_size=20,
                      width=950,
                      height=590,
                      xaxis=dict(
                          title=f"{RS} [cm^-1]",
                          linecolor="#BCCCDC",  # Sets color of X-axis line
                          showgrid=False  # Removes X-axis grid lines
                      ),
                      yaxis=dict(
                          title="Intensity",
                          linecolor="#BCCCDC",  # Sets color of Y-axis line
                          showgrid=True,  # Removes Y-axis grid lines
                      ),
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

                                              )),

    return fig


def draw_plot(df, x, y, plot_color, color='variable'):
    """
    Draws figure from DataFrame with selected x and y, and chosen color
    :param df: DataFrame
    :param x: Str
    :param y: Str
    :param plot_color: List of colors
    :param color: Str
    :return: plotly.graph_objs._figure.Figure
    """

    fig = px.line(df, x=x, y=y, color=color,
                  color_discrete_sequence=plot_color)

    # fig = px.line(df, x=x, y=y, color=color,
    #               color_discrete_sequence=px.colors.cyclical.IceFire)

    return fig


def choose_template():
    """
    Choose default template from the list
    :return: Str, chosen template
    """
    template = st.radio(
        "Choose chart template",
        ('ggplot2', 'seaborn', 'simple_white', 'plotly',
         'plotly_white', 'plotly_dark', 'presentation', 'xgridoff',
         'ygridoff', 'gridon', 'none'), index=1, key='new')
    return template


def plot_color():
    """
    Choose color set for plots
    :return:
    """
    colors = {
        'Plotly': px.colors.qualitative.Plotly,
        'Vivid': px.colors.qualitative.Vivid,
        'Safe': px.colors.qualitative.Safe,
        'Prism': px.colors.qualitative.Prism,
        'Pastel': px.colors.qualitative.Pastel,
        'Bold': px.colors.qualitative.Bold,
        'Antique': px.colors.qualitative.Antique,
        'Set1': px.colors.qualitative.Set1,
        'Set2': px.colors.qualitative.Set2,
        'Set3': px.colors.qualitative.Set3,
        'Pastel2': px.colors.qualitative.Pastel2,
        'Dark2': px.colors.qualitative.Dark2,
        'Pastel1': px.colors.qualitative.Pastel1,
        'Light24': px.colors.qualitative.Light24,
        'Dark24': px.colors.qualitative.Dark24,
        'Alphabet': px.colors.qualitative.Alphabet,
        'T10': px.colors.qualitative.T10,
        'G10': px.colors.qualitative.G10,
        'D3': px.colors.qualitative.D3
    }

    plots_color = st.radio(
        "Choose set of colors for spectra",
        ('Plotly', 'Vivid', 'Safe', 'Prism', 'Pastel', 'Bold', 'Antique', 'Set3', 'Pastel2', 'Set2', 'Dark2', 'Pastel1',
         'Set1', 'Light24', 'Dark24', 'Alphabet', 'T10', 'G10', 'D3'), index=1)

    return colors[plots_color]
