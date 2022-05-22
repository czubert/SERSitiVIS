import streamlit as st
from vis_helpers import vis_utils


def main_page():
    sersitivis_logo = vis_utils.show_sersitivis_logo(width=65, padding=[0, 6, 20, 25], margin=[0, 0, 30, 0])
    st.markdown(sersitivis_logo, unsafe_allow_html=True)
    
    cols = st.columns((1, 6, 1))
    with cols[1]:
        st.subheader("An Application for fast and easy data processing and visualisation")

    cols = st.columns((3, 3, 1))
    with cols[1]:
        st.subheader("By")
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.markdown("")
    
    sersitive_logo = vis_utils.show_logo(width=65, padding=[0, 6, 20, 25], margin=[0, 0, 30, 0])
    st.markdown(sersitive_logo, unsafe_allow_html=True)
    
    st.markdown("")
    st.markdown("")
    st.markdown("")
