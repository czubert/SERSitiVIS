import streamlit as st

from vis_helpers import maps

maps.main(st.session_state.get('df'))
