import base64

import streamlit as st


def sidebar_head():
    st.set_page_config(
        page_title="SERSitive.eu",
        page_icon="https://sersitive.eu/wp-content/uploads/cropped-icon.png",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # radiobuttons in one row
    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
    st.set_option('deprecation.showfileUploaderEncoding', False)
    # linked logo of sersitive at the sidebar
    link = 'http://sersitive.eu'
    
    with open('logos/sersitivis_no_background.png', 'rb') as f:
        data = f.read()
    
    bin_str = base64.b64encode(data).decode()
    html_code = f'''
        <a href="{link}">
            <img src="data:image/png;base64,{bin_str}"
            style="padding:0px 6px 5px 0px; 20px; height:80px"/>
        </a>'''
    
    st.sidebar.markdown(html_code, unsafe_allow_html=True)
    st.sidebar.markdown('')
    st.sidebar.markdown('')
