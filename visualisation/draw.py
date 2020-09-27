import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import inspect

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
                      colorway=px.colors.qualitative.Pastel2,
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


def choosing_colorway():
    all_colors = dict()
    colorscale_names = get_colors_names()

    for el in colorscale_names:
        all_colors[el] = el  # TODO color name as key and color object as a value

    plots_color = st.radio(
        "Choose set of colors for spectra",
        colorscale_names, index=15)

    return all_colors[plots_color]


@st.cache
def get_colors_names():
    colorscale_names = []

    # Plotly express color modules that you can try colors from
    colors_modules = ['diverging', 'qualitative', 'sequential']

    # Getting all colors from modules
    for color_module in colors_modules:
        colorscale_names.extend([f'{color_module}.{name}' for name, body
                                 in inspect.getmembers(getattr(px.colors, color_module))
                                 if isinstance(body, list)])

    return colorscale_names
