import plotly.graph_objects as go


def fig_layout(template, fig, chart_titles=None, plots_colorscale=None):
    """
    Changing layout and styles
    :param template: Str, Plotly template
    :param fig: plotly.graph_objs._figure.Figure
    :param descr: Str
    :return: plotly.graph_objs._figure.Figure
    """
    if chart_titles == None:
        xaxis = (r'Raman Shift cm <sup>-1</sup>')
        yaxis = (r'Intensity [au]')
        title = (r'')
        chart_titles = {'x': xaxis, 'y': yaxis, 'title': title}
    
    fig.update_layout(showlegend=True,
                      template=template,
                      colorway=plots_colorscale,
                      paper_bgcolor='rgba(255,255,255,255)',
                      plot_bgcolor='rgba(255,255,255,255)',
                      width=900,
                      height=550,
                      xaxis=dict(
                          # title=f"{LABELS['RS']} [cm<sup>-1</sup>]",
                          title=f"{chart_titles['x']}",
                          linecolor="#777",  # Sets color of X-axis line
                          showgrid=False,  # Removes X-axis grid lines
                          linewidth=2.5,
                          showline=True,
                          showticklabels=True,
                          ticks='outside',
                      ),
    
                      yaxis=dict(
                          # title="Intensity [au]",
                          # title="Intensity [au]",
                          title=f"{chart_titles['y']}",
                          linecolor="#777",  # Sets color of Y-axis line
                          showgrid=True,  # Removes Y-axis grid lines
                          linewidth=2.5,
                      ),
                      title=go.layout.Title(text=chart_titles['title'],
                                            font=go.layout.title.Font(size=30)),

                      legend=go.layout.Legend(x=0.5, y=0 - .4, traceorder="normal",
                                              font=dict(
                                                  family="sans-serif",
                                                  size=14,
                                                  color="black",

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


