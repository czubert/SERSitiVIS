import inspect

import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

RS = 'Raman Shift'
DS = 'Dark Subtracted #1'
BS = 'Baseline'
FLAT = 'Flattened'
LINE = 'Set thicknes of the line in chart'


def fig_layout(template, fig, plots_colorscale, descr='Chosen spectra'):
    """
    Changing layout and styles
    :param template: Str, Plotly template
    :param fig: plotly.graph_objs._figure.Figure
    :param descr: Str
    :return: plotly.graph_objs._figure.Figure
    """
    fig.update_layout(showlegend=True,
                      template=template,
                      colorway=plots_colorscale,
                      width=950,
                      height=590,
                      xaxis=dict(
                          title=f"{RS} [cm<sup>-1</sup>]",
                          linecolor="#777",  # Sets color of X-axis line
                          showgrid=False,  # Removes X-axis grid lines
                          linewidth=2.5,
                          showline=True,
                          showticklabels=True,
                          ticks='outside',
                      ),

                      yaxis=dict(
                          title="Intensity [au]",
                          linecolor="#777",  # Sets color of Y-axis line
                          showgrid=True,  # Removes Y-axis grid lines
                          linewidth=2.5,
                      ),
                      title=go.layout.Title(text=descr,
                                            font=go.layout.title.Font(size=30)),

                      legend=go.layout.Legend(x=0.5, y=0 - .3, traceorder="normal",
                                              font=dict(
                                                  family="sans-serif",
                                                  size=16,
                                                  color="black"
                                              ),
                                              bgcolor="#fff",
                                              bordercolor="#ccc",
                                              borderwidth=0.4,
                                              orientation='h',
                                              xanchor='auto',
                                              itemclick='toggle',

                                              )),

    fig.update_yaxes(showgrid=True, gridwidth=1.4, gridcolor='#ccc')

    return fig


# Adding traces, spectrum line design
def add_traces_single_spectra(df, fig, x, y, name):
    fig.add_traces(
        [go.Scatter(y=df.reset_index()[y],
                    x=df.reset_index()[x],
                    name=name,
                    line=dict(
                        width=3.5,  # Width of the spectrum line
                        color='#1c336d'  # color of the spectrum line
                        # color='#6C9BC0'  # color of the spectrum line
                    ),
                    )])
    return fig


def add_traces(df, fig, x, y, name, col=None):
    fig.add_traces(
        [go.Scatter(y=df.reset_index()[y],
                    x=df.reset_index()[x],
                    name=name,
                    line=dict(
                        width=3.5,
                    ),
                    )])
    return fig


def choose_template():
    """
    Choose default template from the list
    :return: Str, chosen template
    """
    template = st.radio(
        "Choose chart template",
        list(pio.templates), index=6, key='new')

    return template


def choosing_colorway():
    all_colors = dict()

    # Plotly express color modules that you can try colors from
    modules_colors_l = ['diverging', 'qualitative', 'sequential']
    modules_colors_d = {'diverging': px.colors.diverging,
                        'qualitative': px.colors.qualitative, 'sequential': px.colors.sequential}

    # Getting colors model
    chosen_module_color = st.radio(
        "Choose module of color sets, to see colorsets",
        modules_colors_l, 1)

    colorscale_names = get_colors_names(chosen_module_color)
    for el in colorscale_names:
        all_colors[el] = el  # TODO color name as key and color object as a value


    plots_color = st.radio(
        "Choose set of colors from colorsets for spectra",
        colorscale_names, index=31)

    chosen_color = getattr(modules_colors_d[chosen_module_color], f'{all_colors[plots_color]}')

    return chosen_color


@st.cache
def get_colors_names(chosen_module_color):
    colorscale_names = []

    # Getting all colors from modules
    colorscale_names.extend([f'{name}' for name, body
                             in inspect.getmembers(getattr(px.colors, chosen_module_color))
                             if isinstance(body, list)])

    return colorscale_names
