import base64

import streamlit as st


def trim_spectra(df):
    # trim raman shift range
    min_, max_ = float(df.index.min()), float(df.index.max())
    min_rs, max_rs = st.slider('custom range',
                               min_value=min_, max_value=max_, value=[min_, max_])
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
