import streamlit as st

from vis_helpers.i18n import t

CONTACT_EMAIL = 'developers@sersitive.eu'
AUTHORS = {'Paweł Albrycht': 'https://linkedin.com/in/paweł-albrycht-b791147a',
           'Łukasz Charzewski': 'https://linkedin.com/in/lukasz-charzewski'}


def show_developers():
    """Contact and authors at the bottom of the sidebar"""
    st.sidebar.divider()
    st.sidebar.caption(f'{t("Feedback and questions")}: [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})')
    st.sidebar.caption('By ' + ', '.join(f'[{name}]({url})' for name, url in AUTHORS.items()))
