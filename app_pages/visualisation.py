import streamlit as st

from vis_helpers import visualisation

visualisation.visualisation(st.session_state.get('df'))
