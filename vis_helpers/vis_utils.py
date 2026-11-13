"""
Chart settings and helpers shared by all pages.
"""
import html

import plotly.express as px
import plotly.io as pio
import streamlit as st

from core import processing
from visualisation.draw import fig_layout, is_dark
from vis_helpers.i18n import t, lang

# SERSitive colours first (navy, blue, gold), then well distinguishable ones
SERSITIVE_PALETTE = ['#1C336D', '#6C9BC0', '#DBBD8A', '#B5651D', '#5B8C5A', '#8E6C8A', '#C0504D', '#4BACC6',
                     '#7F7F7F', '#2E2E2E']
# on a dark background navy disappears - lighter shades of the same colours
SERSITIVE_PALETTE_DARK = ['#8DB6D6', '#DBBD8A', '#6C9BC0', '#E0925A', '#86BF85', '#BFA2C9', '#E57F7C', '#4BC0D9',
                          '#B5B5B5', '#ECECEC']


def sersitive_palette():
    return SERSITIVE_PALETTE_DARK if is_dark() else SERSITIVE_PALETTE


PALETTES = {'SERSitive': None,  # resolved for the current theme
            'Plotly': px.colors.qualitative.Plotly,
            'D3': px.colors.qualitative.D3,
            'Safe (colour-blind friendly)': px.colors.qualitative.Safe,
            'Bold': px.colors.qualitative.Bold,
            'Dark24': px.colors.qualitative.Dark24,
            'Viridis': px.colors.sequential.Viridis,
            'Plasma': px.colors.sequential.Plasma,
            'Turbo': px.colors.sequential.Turbo,
            'Custom': None}


def default_titles():
    return {'x': t('Raman Shift [cm<sup>-1</sup>]'), 'y': t('Intensity [a.u.]'), 'title': ''}


def chart_settings(key, titles=None):
    """
    Chart appearance settings (put it inside an expander)
    :param key: Str, unique prefix for widget keys
    :param titles: Dict with default axis titles {'x', 'y', 'title'}
    :return: Dict: palette, template, titles, line_width, image_format
    """
    titles = {**default_titles(), **(titles or {})}
    language = lang()

    palette_name = st.selectbox(t('Colour palette'), list(PALETTES), key=f'{key}_palette')
    if palette_name == 'Custom':
        palette = st.text_input(t('Hexadecimal colors'), '#DB0457 #520185 #780A34 #49BD02 #B25AE8',
                                help=t('Type space separated hexadecimal codes'), key=f'{key}_custom').split()
    else:
        palette = PALETTES[palette_name] or sersitive_palette()
    if st.checkbox(t('Reversed colours'), key=f'{key}_reversed'):
        palette = palette[::-1]

    line_width = st.slider(t('Line width'), 0.5, 5.0, 2.0, 0.5, key=f'{key}_line_width')

    # keys per language - default titles are translated
    chart_titles = {'x': st.text_input(t('X axis title'), titles['x'], key=f'{key}_x_title_{language}'),
                    'y': st.text_input(t('Y axis title'), titles['y'], key=f'{key}_y_title_{language}'),
                    'title': st.text_input(t('Chart title'), titles['title'], key=f'{key}_title_{language}')}

    templates = list(pio.templates)
    default_template = templates.index('plotly_dark' if is_dark() else 'plotly_white')
    template = st.selectbox(t('Chart style'), templates, index=default_template, key=f'{key}_template')

    image_format = st.radio(t('Image format for the camera icon'), ['png', 'svg'], horizontal=True,
                            key=f'{key}_image_format',
                            help=t('Use the camera icon above a chart to save it as an image.'))

    return {'palette': palette, 'template': template, 'titles': chart_titles, 'line_width': line_width,
            'image_format': image_format}


def default_chart_settings():
    return {'palette': sersitive_palette(), 'template': 'plotly_dark' if is_dark() else 'plotly_white',
            'titles': default_titles(),
            'line_width': 2.0, 'image_format': 'png'}


def show_chart(fig, settings, lines=True, **kwargs):
    """
    Applies layout and shows the chart with high resolution image export
    :param fig: plotly Figure
    :param settings: Dict from chart_settings()
    :param lines: Bool, apply line width to the traces
    :param kwargs: passed to st.plotly_chart (e.g. key, on_select)
    """
    fig_layout(settings['template'], fig, chart_titles=settings['titles'], plots_colorscale=settings['palette'])
    if lines:
        fig.update_traces(selector=dict(mode='lines'), line_width=settings['line_width'])
    config = {'displaylogo': False,
              'toImageButtonOptions': {'format': settings['image_format'], 'scale': 3,
                                       'filename': settings['titles']['title'] or 'sersitivis'}}
    return st.plotly_chart(fig, width='stretch', config=config, **kwargs)


def range_slider(label, low, high, key, default=None, **kwargs):
    """
    Range slider which resets itself (to default or full range) when the stored range does not fit new data
    (its value can also be set from a chart selection - see range_from_selection)
    """
    value = st.session_state.get(key)
    if not value or value[0] < low or value[1] > high or value[0] >= value[1]:
        st.session_state[key] = default or (low, high)
    return st.slider(label, min_value=low, max_value=high, key=key, **kwargs)


def spectrum_limits(df):
    return int(float(df.index.min())), int(float(df.index.max())) + 1


def trim_spectra(df, key='range'):
    """Slider for the Raman Shift range"""
    low, high = range_slider(t('Raman Shift range [cm⁻¹]'), *spectrum_limits(df), key=key)
    return processing.trim(df, low, high)


def selected_range(event):
    """
    X range selected on a chart (box selection, or the selected points)
    :param event: value of st.plotly_chart(on_select=...) / its session_state
    :return: (low, high) or None
    """
    if not event:
        return None
    selection = event.get('selection', {}) if isinstance(event, dict) else event.selection
    boxes = selection.get('box') or []
    if boxes and boxes[-1].get('x'):
        x = boxes[-1]['x']
        return min(x), max(x)
    points = [p['x'] for p in selection.get('points') or [] if 'x' in p]
    if len(points) > 1:
        return min(points), max(points)
    return None


def range_from_selection(chart_key, slider_key, low, high):
    """
    on_select callback: copies the range selected on the chart into the range slider
    """
    selected = selected_range(st.session_state.get(chart_key))
    if selected:
        st.session_state[slider_key] = (max(low, int(selected[0])), min(high, int(round(selected[1]))))


def download_csv(df, file_name, label, key, index=True):
    st.download_button(label, data=df.to_csv(index=index).encode('utf-8'), file_name=file_name, mime='text/csv',
                       icon=':material/download:', key=key)


def report_button(key, build, signature):
    """
    'Create PDF report' button + download of the created report.
    The report is dropped when the settings change (signature), so an out-of-date file is never offered.
    :param build: function returning PDF bytes
    :param signature: anything describing the current settings and data
    """
    from datetime import date

    state_key = f'_{key}_report'
    signature = str(signature)
    stored = st.session_state.get(state_key)
    if stored and stored[0] != signature:
        st.session_state.pop(state_key)
        stored = None
    cols = st.columns((1, 1, 2))
    if cols[0].button(t('Create PDF report'), key=f'{key}_report_create', icon=':material/picture_as_pdf:'):
        with st.spinner(t('Creating report...')):
            stored = st.session_state[state_key] = (signature, build())
    if stored:
        cols[1].download_button(t('Download report (PDF)'), stored[1], file_name=f'SERSitiVIS_{key}_{date.today()}.pdf',
                                mime='application/pdf', key=f'{key}_report_download', icon=':material/download:',
                                type='primary')


def _step_spectrum(key, names, delta):
    current = st.session_state.get(key)
    i = names.index(current) if current in names else 0
    st.session_state[key] = names[(i + delta) % len(names)]


def spectrum_stepper(names, key):
    """
    Pick one spectrum with ‹ › arrows (wraps around) instead of a drop-down list.
    :param names: list of spectrum names
    :param key: session_state key holding the chosen name
    :return: chosen name
    """
    names = list(names)
    if st.session_state.get(key) not in names:
        st.session_state[key] = names[0]
    name = st.session_state[key]
    left, middle, right = st.columns((1, 4, 1), vertical_alignment='center', gap='small')
    left.button('', icon=':material/chevron_left:', key=f'{key}_prev', help=t('Previous spectrum'),
                on_click=_step_spectrum, args=(key, names, -1), use_container_width=True)
    right.button('', icon=':material/chevron_right:', key=f'{key}_next', help=t('Next spectrum'),
                 on_click=_step_spectrum, args=(key, names, 1), use_container_width=True)
    middle.html(f'<div title="{html.escape(name)}" style="text-align: center; line-height: 1.25;">'
                f'<div style="font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">'
                f'{html.escape(name)}</div>'
                f'<div style="font-size: 0.8rem; opacity: 0.65;">{names.index(name) + 1} / {len(names)}</div></div>')
    return name
