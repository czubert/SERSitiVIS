import streamlit as st

from vis_helpers import workspace
from vis_helpers.i18n import t

SERSITIVE_URL = 'https://sersitive.eu'
CONTACT_EMAIL = 'developers@sersitive.eu'
SPECTROMETERS = ['BWTEK', 'Renishaw', 'WITec', 'Wasatch', 'Jobin Yvon', 'Teledyne Princeton Instruments']


def main(visualisation_page="app_pages/visualisation.py"):
    """
    :param visualisation_page: page to open after loading example data
    """
    st.image('logos/sersitivis_no_background.png', width=420)
    st.subheader(t('Fast and easy processing and visualisation of Raman and SERS spectra'))
    st.write('')

    steps = [(':material/upload_file:', t('Upload spectra'),
              t('Drop *.txt or *.csv files in the sidebar. The spectrometer type is detected automatically.')),
             (':material/query_stats:', t('Choose analysis'),
              t('Visualise and process spectra, check reproducibility (RSD), calculate the Enhancement Factor '
                'or run PCA.')),
             (':material/download:', t('Download results'),
              t('Export charts (PNG, SVG) and processed data (CSV).'))]

    for col, (icon, title, text) in zip(st.columns(3), steps):
        with col.container(border=True):
            st.markdown(f'#### {icon} {title}')
            st.write(text)

    st.write('')
    if st.button(t('Try with example data'), type='primary', icon=':material/play_arrow:',
                 on_click=workspace.load_example, args=(workspace.DEFAULT_EXAMPLE,)):
        st.switch_page(visualisation_page)

    st.caption(f'{t("Supported spectrometers")}: {", ".join(SPECTROMETERS)}, {t("other text tables")}')

    st.divider()
    with st.container(border=True):
        cols = st.columns((3, 1), vertical_alignment='center')
        with cols[0]:
            st.markdown(f'#### {t("Need SERS substrates?")}')
            st.write(t('SERSitive makes reproducible silver and gold SERS substrates.'))
        with cols[1]:
            st.link_button(t('Visit SERSitive'), SERSITIVE_URL, icon=':material/open_in_new:', width='stretch')
