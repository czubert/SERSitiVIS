import streamlit as st

from processing import utils
from . import draw

P3D = "Plot 3D"
RS = "Raman Shift"
DEG = "Polynominal degree"
WINDOW = "Set window for spectra flattening"
FLAT = "Flattened"
COR = "Corrected"


def show_3d_plots(df, plots_color, template, _):
    df2 = df.copy()
    df2.columns = ['widmo nr ' + str(i) for i in range(len(df2.columns))]
    import plotly.express as px
    # Adding possibility to change degree of polynominal regression
    deg, window = utils.adjust_spectras_by_window_and_degree()

    # Baseline correction + flattening
    df2 = utils.correct_baseline(df=df2, deg=deg)
    df2 = utils.smoothen_the_spectra(df=df2, window=window)
    # drawing a plot
    df2 = df2.reset_index()
    df2m = df2.melt('Raman Shift', df2.columns[1:])
    df2m_drop = df2m.dropna()

    fig_3d = px.line_3d(df2m_drop, x='variable', y=RS, z='value', color='variable')

    draw.fig_layout(template, fig_3d, plots_colorscale=plots_color,
                    descr=f'{P3D} with {COR} + {FLAT} spectra')
    
    camera = dict(
        eye=dict(x=1.9, y=0.15, z=0.2)
    )
    
    fig_3d.update_layout(scene_camera=camera,
                         width=900,
                         height=900,
                         margin=dict(l=1, r=1, t=30, b=1),
                         )
    st.write(fig_3d)