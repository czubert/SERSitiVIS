import base64

import plotly.express as px
import plotly.io as pio
import streamlit as st


def trim_spectra(df):
    # trim raman shift range
    min_, max_ = float(df.index.min()), float(df.index.max())
    min_max = st.slider('Custom range',
                        min_value=min_, max_value=max_, value=[min_, max_])
    min_rs, max_rs = min_max.split('__')
    min_rs, max_rs = float(min_rs), float(max_rs)
    mask = (min_rs <= df.index) & (df.index <= max_rs)
    return df[mask]


@st.cache
def show_logo():
    with open('logos/logo.png', 'rb') as f:
        data = f.read()

    bin_str = base64.b64encode(data).decode()
    html_code = f'''
                    <img src="data:image/png;base64,{bin_str}"
                    style="
                         margin: auto;
                         margin-top:-30px;
                         width: 65%;
                         padding:0px 6px 20px 25%;
                         "/>
                '''
    return html_code


@st.cache
def show_sersitivis_logo():
    link = 'http://sersitive.eu'

    with open('logos/sersitivis_no_background.png', 'rb') as f:
        data = f.read()

    bin_str = base64.b64encode(data).decode()
    html_code = f'''
        <a href="{link}" target = _blank>
            <img src="data:image/png;base64,{bin_str}"
            style="padding:0px 6px 5px 0px; 20px; height:80px"/>
        </a>'''

    return html_code


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

    palette_module = getattr(px.colors, palette_type)
    palette = getattr(palette_module, palette)

    return palette, template


def get_chart_vis_properties_vis():
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
    print_widget_labels('Colors')
    palette_type = st.selectbox("Type of color palette", list(palettes.keys()), 0)
    palette = st.selectbox("Color palette", palettes[palette_type], index=0)
    if st.checkbox('Reversed', False):
        palette = palette + '_r'
    print_widgets_separator(2)
    print_widget_labels('Template')
    template = choose_template()
    print_widgets_separator(2)

    palette_module = getattr(px.colors, palette_type)
    palette = getattr(palette_module, palette)

    return palette, template


def print_widgets_separator(n=1, sidebar=False):
    """
    Prints customized separation line on sidebar
    """
    html = """<hr style="height:1px;
            border:none;color:#fff;
            background-color:#999;
            margin-top:5px;
            margin-bottom:10px" 
            />"""

    for _ in range(n):
        if sidebar:
            st.sidebar.markdown(html, unsafe_allow_html=True)
        else:
            st.markdown(html, unsafe_allow_html=True)

def print_widget_labels(widget_title, margin_top=5, margin_bottom=10):
    """
    Prints Widget label on the sidebar and lets adjust its margins easily
    :param widget_title: Str
    """
    st.markdown(
        f"""<p style="font-weight:500; margin-top:{margin_top}px;margin-bottom:{margin_bottom}px">{widget_title}</p>""",
        unsafe_allow_html=True)
