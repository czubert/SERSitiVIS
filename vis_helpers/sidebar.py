import streamlit as st

from vis_helpers import vis_utils


def sidebar_head():
    """
    Sets Page title, page icon, layout, initial_sidebar_state
    Sets position of radiobuttons (in a row or one beneath another)
    Shows logo in the sidebar
    """
    st.set_page_config(
        page_title="SERSitive.eu",
        page_icon="https://sersitive.eu/wp-content/uploads/cropped-icon.png",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # radiobuttons in one row
    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
    st.set_option('deprecation.showfileUploaderEncoding', False)
    
    # SERSitivis logo
    html_code = vis_utils.show_sersitivis_logo()
    
    st.sidebar.markdown(html_code, unsafe_allow_html=True)
    st.sidebar.markdown('')
    st.sidebar.markdown('')
