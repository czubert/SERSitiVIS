import plotly.graph_objects as go
import streamlit as st


def is_dark():
    """True when the viewer uses the dark theme"""
    try:
        return st.context.theme.type == 'dark'
    except Exception:
        return False


def theme_colors():
    if is_dark():
        return {'text': '#DCE2EA', 'axis': '#7A8696', 'grid': '#2C3440'}
    return {'text': '#1F2329', 'axis': '#777777', 'grid': '#E3E6EA'}


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

    colors = theme_colors()
    fig.update_layout(showlegend=fig.layout.showlegend is not False,
                      template=template,
                      colorway=plots_colorscale,
                      paper_bgcolor='rgba(0,0,0,0)',  # transparent - the app background shows through
                      plot_bgcolor='rgba(0,0,0,0)',
                      height=fig.layout.height or 550,
                      font=dict(family='sans-serif', size=14, color=colors['text']),
                      margin=dict(t=60 if chart_titles['title'] else 30),
                      xaxis=dict(title=chart_titles['x'],
                                 linecolor=colors['axis'],
                                 showgrid=False,
                                 linewidth=2,
                                 showline=True,
                                 ticks='outside'),
                      yaxis=dict(title=chart_titles['y'],
                                 linecolor=colors['axis'],
                                 linewidth=2,
                                 showline=True,
                                 showgrid=True,
                                 gridwidth=1,
                                 gridcolor=colors['grid']),
                      title=go.layout.Title(text=chart_titles['title'], font=dict(size=22)),
                      legend=go.layout.Legend(orientation='h', x=0.5, xanchor='center', y=-0.28, yanchor='top',
                                              title_text='', font=dict(size=13), itemclick='toggle'),
                      hovermode='x')

    fig.update_traces(hovertemplate=None)
    return fig
