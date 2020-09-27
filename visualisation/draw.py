import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

import streamlit as st

RS = 'Raman Shift'
DS = 'Dark Subtracted #1'
BS = 'Baseline'
FLAT = 'Flattened'


def fig_layout(template, fig, plots_colorscale, descr='Chosen spectra'):
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
                      coloraxis=dict(colorscale=plots_colorscale),
                      width=1050,
                      height=590,
                      xaxis=dict(
                          title=f"{RS} [cm^-1]",
                          linecolor="#BCCCDC",  # Sets color of X-axis line
                          showgrid=False  # Removes X-axis grid lines
                      ),
                      yaxis=dict(
                          title="Intensity [au]",
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


def add_traces(df, fig, x, y, name, col=None):
    fig.add_traces([go.Scatter(y=df.reset_index()[y], x=df.reset_index()[x], name=name)])
    return fig


def choose_template():
    """
    Choose default template from the list
    :return: Str, chosen template
    """
    template = st.radio(
        "Choose chart template",
        list(pio.templates), index=1, key='new')
    return template


def plot_colorscale():
    """
    Choose color set for plots
    :return: String
    """
    color_list = ['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance', 'blackbody',
                  'bluered', 'blues', 'blugrn', 'bluyl', 'brbg', 'brwnyl', 'bugn', 'bupu',
                  'burg', 'burgyl', 'cividis', 'curl', 'darkmint', 'deep', 'delta', 'dense',
                  'earth', 'edge', 'electric', 'emrld', 'fall', 'geyser', 'gnbu', 'gray',
                  'greens', 'greys', 'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno',
                  'jet', 'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
                  'orrd', 'oryel', 'peach', 'phase', 'picnic', 'pinkyl', 'piyg', 'plasma',
                  'plotly3', 'portland', 'prgn', 'pubu', 'pubugn', 'puor', 'purd', 'purp',
                  'purples', 'purpor', 'rainbow', 'rdbu', 'rdgy', 'rdpu', 'rdylbu', 'rdylgn',
                  'redor', 'reds', 'solar', 'spectral', 'speed', 'sunset', 'sunsetdark', 'teal',
                  'tealgrn', 'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid', 'twilight',
                  'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd']

    colors = {}

    for el in color_list:
        colors[el] = el

    plots_color = st.radio(
        "Choose set of colors for spectra",
        color_list, index=15)

    return colors[plots_color]
