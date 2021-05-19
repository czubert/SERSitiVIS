import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from constants import LABELS


def fig_layout(template, fig, plots_colorscale, descr=None):
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
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)',
                      width=900,
                      height=470,
                      xaxis=dict(
                          title=f"{LABELS['RS']} [cm<sup>-1</sup>]",
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

    # plain hover
    fig.update_traces(hovertemplate=None)
    fig.update_layout(hovermode="x")
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
    template = st.selectbox(
        "Choose chart template",
        list(pio.templates), index=6, key='new')

    return template


def get_chart_vis_properties():
    palettes = {
        'qualitative': ['Alphabet', 'Antique', 'Bold', 'D3', 'Dark2', 'Dark24', 'G10', 'Light24', 'Pastel',
                        'Pastel1', 'Pastel2', 'Plotly', 'Prism', 'Safe', 'Set1', 'Set2', 'Set3', 'T10', 'Vivid',
                        ],
        'diverging': ['Armyrose', 'BrBG', 'Earth', 'Fall', 'Geyser', 'PRGn', 'PiYG', 'Picnic', 'Portland', 'PuOr',
                      'RdBu', 'RdGy', 'RdYlBu', 'RdYlGn', 'Spectral', 'Tealrose', 'Temps', 'Tropic', 'balance',
                      'curl', 'delta', 'oxy',
                      ],
        'sequential': ['Aggrnyl', 'Agsunset', 'Blackbody', 'Bluered', 'Blues', 'Blugrn', 'Bluyl', 'Brwnyl', 'BuGn',
                       'BuPu', 'Burg', 'Burgyl', 'Cividis', 'Darkmint', 'Electric', 'Emrld', 'GnBu', 'Greens', 'Greys',
                       'Hot', 'Inferno', 'Jet', 'Magenta', 'Magma', 'Mint', 'OrRd', 'Oranges', 'Oryel', 'Peach',
                       'Pinkyl', 'Plasma', 'Plotly3', 'PuBu', 'PuBuGn', 'PuRd', 'Purp', 'Purples', 'Purpor', 'Rainbow',
                       'RdBu', 'RdPu', 'Redor', 'Reds', 'Sunset', 'Sunsetdark', 'Teal', 'Tealgrn', 'Turbo', 'Viridis',
                       'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd', 'algae', 'amp', 'deep', 'dense', 'gray', 'haline', 'ice',
                       'matter', 'solar', 'speed', 'tempo', 'thermal', 'turbid',
                       ]
    }
    
    col1, col2, col3 = st.beta_columns(3)
    
    with col1:
        palette_type = st.selectbox("Type of color palette", list(palettes.keys()), 0)
    with col2:
        palette = st.selectbox("Color palette", palettes[palette_type], index=0)
        if st.checkbox('Reversed', False):
            palette = palette + '_r'
    with col3:
        template = choose_template()
    # with col4:
    
    palette_module = getattr(px.colors, palette_type)
    palette = getattr(palette_module, palette)
    
    return palette, template
