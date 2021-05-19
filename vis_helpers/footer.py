import streamlit as st
from htbuilder.units import percent, px

#
# def image(src_as_string, **style):
#     return img(src=src_as_string, style=styles(**style))
#
#
# def link(link, text, **style):
#     return a(_href=link, _target="_blank", style=styles(**style))(text)
#
#
# def layout(*args):
#     style = """
#     <style>
#       # MainMenu {visibility: hidden;}
#       footer {visibility: hidden;}
#      .stApp { bottom: 0px; }
#     </style>
#     """
#
#     style_div = styles(
#         position="fixed",
#         left=0,
#         bottom=0,
#         margin=px(0, 0, 0, 0),
#         width=percent(100),
#         color="black",
#         text_align="center",
#         height="auto",
#         opacity=1,
#     )
#
#     style_hr = styles(
#         display="block",
#         margin=px(8, 8, "auto", "auto"),
#         border_width=px(2)
#     )
#
#     body = p()
#     foot = div(
#         style=style_div
#     )(
#         hr(
#             style=style_hr
#         ),
#         body
#     )
#
#     st.markdown(style, unsafe_allow_html=True)
#
#     for arg in args:
#         if isinstance(arg, str):
#             body(arg)
#
#         elif isinstance(arg, HtmlElement):
#             body(arg)
#
#     st.markdown(str(foot), unsafe_allow_html=True)
#
#
# def footer():
#     myargs = [
#         "Made in ",
#         image('https://avatars3.githubusercontent.com/u/45109972?s=400&v=4',
#               width=px(25), height=px(25)),
#         " with ❤️ by ",
#         link("https://twitter.com/ChristianKlose3", "@ChristianKlose3"),
#         br(),
#         link("https://buymeacoffee.com/chrischross", image('https://i.imgur.com/thJhzOO.png')),
#     ]
#     layout(*myargs)
#
# if __name__ == "__main__":
#     footer()


import streamlit as st
from htbuilder import HtmlElement, div, ul, li, br, hr, a, p, img, styles, classes, fonts
from htbuilder.units import percent, px


def image(src_as_string, **style):
    return img(src=src_as_string, style=styles(**style))


def link(link, text, **style):
    return a(_href=link, _target="_blank", style=styles(**style))(text)


def layout(*args):
    style = """
    <style>
      # MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
    </style>
    """
    
    style_div = styles(
        left=0,
        bottom=0,
        margin=px(0, 0, -1000, 0),
        width=percent(100),
        text_align="center",
        height="0px",
        opacity=0.8
    )
    
    style_hr = styles(
    )
    
    body = p()
    foot = div(style=style_div)(hr(style=style_hr), body)
    
    st.markdown(style, unsafe_allow_html=True)
    
    for arg in args:
        if isinstance(arg, str):
            body(arg)
        elif isinstance(arg, HtmlElement):
            body(arg)
    
    st.markdown(str(foot), unsafe_allow_html=True)


def footer():
    myargs = [
        "<b>Provided by</b>: ",
        link("https://www.sersitive.eu/",
             image('https://sersitive.eu/wp-content/uploads/logo-przyciete-przesuniete-male_na-strone-1-300x68.png',
                   width=px(120), height=px(25), margin=px(0, 10, 0, 0))),
        ", SERSitiVIS ",
        link("https://share.streamlit.io/czubert/sersitivis/vis.py", image('./logos/logo.png',
                                                                           width=px(24), height=px(25),
                                                                           margin=px(0, 10, 0, 0))),
        ", SERSitive Developers Squad",
        link("https://www.docker.com/", image(
            'https://www.docker.com/sites/default/files/d8/styles/role_icon/public/2019-07/Moby-logo.png?itok=sYH_JEaJ',
            width=px(20), height=px(18), margin=px(0, 10, 0, 0))),
        br(),
    ]
    layout(*myargs)

# if __name__ == "__main__":
#     footer()
