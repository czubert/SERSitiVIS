import plotly.graph_objects as go


def fig_layout(template, fig, chart_titles=None, plots_colorscale=None):
    """
    Common layout and style of the charts
    :param template: Str, Plotly template
    :param fig: plotly Figure
    :param chart_titles: Dict {'x', 'y', 'title'}
    :param plots_colorscale: List of colours
    :return: plotly Figure
    """
    if chart_titles is None:
        chart_titles = {'x': 'Raman Shift [cm<sup>-1</sup>]', 'y': 'Intensity [a.u.]', 'title': ''}

    fig.update_layout(showlegend=True,
                      template=template,
                      colorway=plots_colorscale,
                      paper_bgcolor='white',
                      plot_bgcolor='white',
                      height=fig.layout.height or 550,
                      font=dict(family='sans-serif', size=14),
                      margin=dict(t=60 if chart_titles['title'] else 30),
                      xaxis=dict(title=chart_titles['x'],
                                 linecolor='#777',
                                 showgrid=False,
                                 linewidth=2,
                                 showline=True,
                                 ticks='outside'),
                      yaxis=dict(title=chart_titles['y'],
                                 linecolor='#777',
                                 linewidth=2,
                                 showline=True,
                                 showgrid=True,
                                 gridwidth=1,
                                 gridcolor='#e5e5e5'),
                      title=go.layout.Title(text=chart_titles['title'], font=dict(size=22)),
                      legend=go.layout.Legend(orientation='h', x=0.5, xanchor='center', y=-0.2, yanchor='top',
                                              title_text='', font=dict(size=13), itemclick='toggle'),
                      hovermode='x')

    fig.update_traces(hovertemplate=None)
    return fig
