import streamlit as st

from vis_helpers import rsd

rsd.main(st.session_state.get('df'))
