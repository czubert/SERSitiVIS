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

    # SERSitivis logo
    html_code = vis_utils.show_sersitivis_logo()

    st.sidebar.markdown(html_code, unsafe_allow_html=True)
    st.sidebar.markdown('')
    st.sidebar.markdown('')


def print_widgets_separator():
    st.sidebar.markdown(
        """<hr style="height:1px;border:none;color:#fff;background-color:#999;margin-top:5px;margin-bottom:10px" /> """,
        unsafe_allow_html=True)


def print_widget_labels(widget_title, margin_top=5, margin_bottom=10):
    """
    Prints Widget label on the sidebar
    :param widget_title: Str
    """
    st.sidebar.markdown(
        f"""<p style="font-weight:500; margin-top:{margin_top}px;margin-bottom:{margin_bottom}px">{widget_title}</p>""",
        unsafe_allow_html=True)
