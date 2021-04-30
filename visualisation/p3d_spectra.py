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
    df = df.copy()
    df.columns = ['widmo nr ' + str(i) for i in range(len(df.columns))]
    import plotly.express as px
    # Adding possibility to change degree of polynominal regression
    deg, window = utils.degree_and_window_sliders()
    
    # Baseline correction + flattening
    df = utils.subtract_baseline(df=df, deg=deg)
    df = utils.smoothen_the_spectra(df=df, window=window)
    # drawing a plot
    df = df.reset_index()
    dfm = df.melt('Raman Shift', df.columns[1:])
    dfm_drop = dfm.dropna()
    
    fig_3d = px.line_3d(dfm_drop, x='variable', y=RS, z='value', color='variable')
    
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
