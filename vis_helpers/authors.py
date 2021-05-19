import streamlit as st

authors_css = """
        style='
        display: block;
        font-weight: 400;
        font-size:1.1em;
        color:#DBBD8A;
        filter: brightness(85%);
        text-align: center;
        text-decoration: none;
        a.a:hover{color: red}
        '
"""

def made_by():
    """
    Shows formatted 'by'
    """
    st.sidebar.markdown(f"\n\n\n")
    st.sidebar.markdown(
        '<p ' + authors_css + '>' + 'By </p>',
        unsafe_allow_html=True)


def made_by_pawel():
    """
    Shows formated text, linked with https address
    """
    st.sidebar.markdown(
        '<a ' + authors_css + ' target="_blank" href="https://linkedin.com/in/paweł-albrycht-b791147a">' + 'Paweł Albrycht</a>',
        unsafe_allow_html=True,
    )


def made_by_lukasz():
    """
    Shows formated text, linked with https address
    """
    st.sidebar.markdown(
        "<a " + authors_css + ' target="_blank" href="https://linkedin.com/in/lukasz-charzewski">' + "Łukasz Charzewski</a>",
        unsafe_allow_html=True,
    )

# TODO nie wiem jak zrobić, żeby ten mail dzialal po przycisnieciu
def contact_developers():
    """
    Shows formated text, linked with email address
    """
    st.subheader('')
    st.subheader('')
    
    st.markdown('#### We will appreciate :raised_hands: any feedback from you, please contact:')
    st.markdown(
        "<a " + authors_css + ' href="mailto:developers[at]sersitive.eu">' + "SERSitive Developers</a>",
        unsafe_allow_html=True,
    )


def show_developers():
    """
    Shows all the links and mails to developers
    :return:
    """
    # contact_developers()
    
    made_by()
    made_by_pawel()
    made_by_lukasz()
