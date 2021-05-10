import streamlit as st


def made_by():
    st.sidebar.markdown(f"\n\n\n")
    st.sidebar.markdown(
        """<p style='display: block; text-align: center; color:#DBBD8A; text-decoration: none;'>by</p>""",
        unsafe_allow_html=True)


def made_by_pawel():
    st.sidebar.markdown(
        """<a style='
        display: block;
        text-align: center;
        color:#DBBD8A;
        text-decoration: none;
        :hover {color: red}
        :visited:hover {color: purple}
        '
        target="_blank"
        href="https://linkedin.com/in/paweł-albrycht-b791147a">Paweł Albrycht</a>
        """,
        unsafe_allow_html=True,
    )


def made_by_lukasz():
    st.sidebar.markdown(
        """<a style='
        display: block;
        text-align: center;
        color:#DBBD8A;
        text-decoration: none;
        :hover {color: red}
        :visited:hover {color: purple}
        '
        target="_blank"
        href="https://linkedin.com/in/lukasz-charzewski">Łukasz Charzewski</a>
        """,
        unsafe_allow_html=True,
    )


def contact_developers():
    st.subheader('')
    
    st.markdown('#### We will appreciate :raised_hands: any feedback from you, please contact:')
    st.markdown(
        """
        <a style='
        display: block;
        text-align: center;
        color:#DBBD8A;
        text-decoration: none;
        :hover {color: red}
        :visited:hover {color: purple}
        '
        target="_self"
        href="mailto:developers@sersitive.eu"> SERSitive Developers</a>
        """,
        unsafe_allow_html=True,
    )


def show_developers():
    contact_developers()

    made_by()
    made_by_pawel()
    made_by_lukasz()