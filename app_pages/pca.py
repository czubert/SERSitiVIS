import streamlit as st

from vis_helpers import pca

pca.main(st.session_state.get('df'))
