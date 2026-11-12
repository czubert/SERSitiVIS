import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA
import streamlit as st

from core import processing
from . import vis_utils, data_customisation
from visualisation.draw import fig_layout
from vis_helpers.vis_utils import print_widgets_separator


def main(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    st.write('## PCA Analysis')
    print_widgets_separator(1, sidebar=False)

    if df is None:
        st.warning('Upload spectra in the sidebar (or choose example data)')
        return

    if df.shape[1] < 2:
        st.warning('PCA needs at least two spectra')
        return

    rescale = st.sidebar.checkbox("Rescale")
    baseline_correction = st.sidebar.checkbox("Baseline correction")

    cols = st.columns(2)
    with cols[0]:
        groups_num = int(st.slider('Number of groups', 1, 6, value=min(2, df.shape[1])))
    with cols[1]:
        components_num = int(st.slider('Principal components', 1, 3, value=2))

    print_widgets_separator(1, sidebar=False)

    # Assign spectra to groups. Default: spectra split in order into equal parts
    # (files are usually uploaded group by group)
    default_split = np.array_split(np.array(df.columns), groups_num)
    group_names, group_spectra = [], []
    for i, col in enumerate(st.columns(groups_num)):
        with col:
            group_names.append(st.text_input('Group name', f'{i + 1}', key=f'pca_group_name_{i}'))
            group_spectra.append(st.multiselect('Spectra', list(df.columns), default=list(default_split[i]),
                                                key=f'pca_group_{groups_num}_{i}'))

    print_widgets_separator(1, sidebar=False)

    selected = [spectrum for spectra in group_spectra for spectrum in spectra]
    if len(selected) != len(set(selected)):
        st.warning('Each spectrum can belong to one group only')
        return
    if len(selected) < max(2, components_num):
        st.warning(f'Choose at least {max(2, components_num)} spectra')
        return

    df = df[selected]
    group = [name for name, spectra in zip(group_names, group_spectra) for _ in spectra]

    if rescale:
        df = processing.normalize(df)

    if baseline_correction:
        with st.sidebar.expander('Change Baseline Correction Properties'):
            deg = data_customisation.choosing_regression_degree()
            window = data_customisation.choosing_smoothening_window()
        _, _, df = processing.baseline_and_smooth(df, {col: (deg, window) for col in df.columns})

    cols = st.columns((2, 1))
    with cols[1]:
        st.markdown("# ")
        with st.expander("Customize all charts"):
            plot_palette, plot_template = vis_utils.get_chart_vis_properties_vis()
            chart_titles = vis_utils.get_plot_description_pca()

    model = PCA(components_num)

    trans_data = model.fit_transform(df.fillna(0).T)
    trans_df = pd.DataFrame(trans_data, index=df.columns, columns=[f'PC {i}' for i in range(1, components_num + 1)])

    if components_num == 1:
        fig = px.scatter(trans_df, x='PC 1', color=group, color_discrete_sequence=plot_palette)
    elif components_num == 2:
        fig = px.scatter(trans_df, x='PC 1', y='PC 2', color=group, color_discrete_sequence=plot_palette)
    else:
        fig = px.scatter_3d(trans_df, x='PC 1', y='PC 2', z='PC 3', color=group, color_discrete_sequence=plot_palette)

    fig_layout(plot_template, fig, chart_titles=chart_titles, plots_colorscale=plot_palette)
    fig.layout.legend.title = 'Group:'
    var_df = pd.DataFrame(model.explained_variance_ratio_,
                          index=trans_df.columns, columns=['ratio of explained variance'])

    with cols[0]:
        st.plotly_chart(fig, width='stretch')

        with st.expander("Uploaded spectra"):
            fig = px.line(df, x=df.index, y=df.columns)
            fig_layout(plot_template, fig, plots_colorscale=plot_palette)
            st.plotly_chart(fig, width='stretch')

        with st.expander("Inverse-transformed spectra"):
            reversed_data = model.inverse_transform(trans_df)
            reversed_df = pd.DataFrame(reversed_data, columns=df.index, index=df.columns).T
            fig = px.line(reversed_df, x=reversed_df.index, y=reversed_df.columns)
            fig_layout(plot_template, fig, plots_colorscale=plot_palette)
            st.plotly_chart(fig, width='stretch')

        with st.expander("Show PCA details"):
            st.table(var_df)
            st.write(trans_df.assign(group=group))
