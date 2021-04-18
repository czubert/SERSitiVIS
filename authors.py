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
        href="linkedin.com/in/lukasz-charzewski">Paweł Albrycht</a>
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
        href="linkedin.com/in/lukasz-charzewski">Łukasz Charzewski</a>
        """,
        unsafe_allow_html=True,
    )
