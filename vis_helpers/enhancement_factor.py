import streamlit as st
from vis_helpers.enhancement_factor_utils import calculate_enhancement


def main():
    c = 1e-6
    v = 2
    l_nm = 785
    na = 0.40
    surface_coverage = 0.1
    # surface 5mm x 4 mm x 2 because of the surface roughness
    active_area = 5 * 4 * 2
    i_sers = 60000
    i_raman = 1000
    
    st.write(calculate_enhancement(c, v, l_nm, na, active_area, surface_coverage, i_sers, i_raman) / 1e+8)
