"""
SERSitiVIS - entry point. Run with:  streamlit run vis.py
"""
import os

import sentry_sdk
import streamlit as st

from vis_helpers import authors, i18n, workspace
from vis_helpers.i18n import t

if os.path.isfile(".streamlit/secrets.toml") and 'sentry_url' in st.secrets:
    sentry_sdk.init(st.secrets['sentry_url'], traces_sample_rate=0.001)


def main():
    st.set_page_config(page_title="SERSitiVIS | SERSitive.eu",
                       page_icon="https://sersitive.eu/wp-content/uploads/cropped-icon.png",
                       layout="wide")
    st.logo('logos/sersitivis_no_background.png', link='https://sersitive.eu', size='large')
    # st.logo is only 32 px high - too small for the SERSitiVIS logo (the tagline becomes a blur)
    st.html('<style>'
            '[data-testid="stSidebarHeader"] {height: auto; align-items: flex-start;}'
            '[data-testid="stLogoLink"] {flex: 1 1 auto; max-width: 210px;}'
            '[data-testid="stSidebarLogo"] {height: auto; width: 100%; max-width: none; max-height: none;}'
            '</style>')

    pages = [
        st.Page('app_pages/start.py', title=t('Start'), icon=':material/home:', default=True),
        st.Page('app_pages/visualisation.py', title=t('Visualisation'), icon=':material/show_chart:',
                url_path='visualisation'),
        st.Page('app_pages/rsd.py', title=t('RSD'), icon=':material/stacked_line_chart:', url_path='rsd'),
        st.Page('app_pages/enhancement_factor.py', title=t('Enhancement Factor'), icon=':material/bolt:',
                url_path='enhancement_factor'),
        st.Page('app_pages/pca.py', title=t('PCA'), icon=':material/scatter_plot:', url_path='pca'),
    ]
    page = st.navigation(pages)

    i18n.language_selector()

    # Spectra uploaded once, shared by all pages
    st.session_state['df'] = workspace.data_sidebar()

    page.run()
    authors.show_developers()


main()
