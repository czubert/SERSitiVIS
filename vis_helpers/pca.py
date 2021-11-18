import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
import streamlit as st


import processing
from constants import LABELS
from . import sidebar, vis_utils
from visualisation.draw import fig_layout
from processing import utils
from vis_helpers.vis_utils import print_widgets_separator


def main():
    spectra_types = ['EMPTY', 'BWTEK', 'RENI', 'WITEC', 'WASATCH', 'TELEDYNE', 'JOBIN']
    
    st.write('## PCA Analysis')

    print_widgets_separator(1, sidebar=False)
    
    rescale = st.sidebar.checkbox("Rescale")
    baseline_correction = st.sidebar.checkbox("Baseline correction")
    
    # Choose plot colors and templates
    # with main_expander:
    #     plot_palette, plot_template = vis_utils.get_chart_vis_properties()
    
    cols = st.beta_columns(2)
    
    with cols[0]:
        groups_num = st.slider('Number of groups', 1, 6, value=2)
        groups_num = int(groups_num)
    
    with cols[1]:
        components_num = st.slider('Principal components', 1, 3, value=2)
        components_num = int(components_num)
    
    print_widgets_separator(1, sidebar=False)
    
    cols = st.beta_columns(groups_num)
    dfs = []
    group_names = []
    for col_ind, col in enumerate(cols):
        with col:
            files = st.file_uploader(label='Upload data',
                                     accept_multiple_files=True,
                                     type=['txt', 'csv'],
                                     key=f'uploader_{col_ind}'
                                     )
            
            spectrometer = st.selectbox("Choose spectra type",
                                        spectra_types,
                                        format_func=LABELS.get,
                                        index=1,
                                        key=col
                                        )
            group_name = st.text_input("Provide group name", f"{col_ind}")
            group_names.append(group_name)
            
            if files:
                df = processing.save_read.files_to_df(files, spectrometer)
                dfs.append(df)

    print_widgets_separator(1, sidebar=False)

    if len(dfs) < groups_num:
        return

    df = pd.concat(dfs, axis=1)
    df = df.interpolate().bfill().ffill()

    # Possibility to put a name of a group in PCA, beneath the file uploader - more visible on the plot
    group = [group_names[i] for i in range(groups_num) for _ in dfs[i].columns]

    if rescale:
        scaler = MinMaxScaler()
        rescaled_data = scaler.fit_transform(df)
        df = pd.DataFrame(rescaled_data, columns=df.columns, index=df.index)

    if baseline_correction:
        baseline_corr_properties = st.sidebar.beta_expander('Change Baseline Correction Properties')
        with baseline_corr_properties:
            deg = utils.choosing_regression_degree()
            window = utils.choosing_smoothening_window()
            vals = {'col': (deg, window)}

        *_, df = vis_utils.subtract_baseline_and_smoothen(df, vals, cols_name=True)
    
    cols = st.beta_columns((2, 1))
    with cols[1]:
        st.markdown("# ")
        with st.beta_expander("Customize all charts"):
            plot_palette, plot_template = vis_utils.get_chart_vis_properties_vis()
            chart_titles = vis_utils.get_plot_description_pca()
    
    model = PCA(components_num)
    
    trans_data = model.fit_transform(df.fillna(0).T)
    trans_df = pd.DataFrame(trans_data, index=df.columns, columns=[f'PC {i}' for i in range(1, components_num + 1)])
    
    if components_num == 1:
        fig = px.scatter(trans_df, x='PC 1', color=group, color_discrete_sequence=plot_palette)
    elif components_num == 2:
        fig = px.scatter(trans_df, x='PC 1', y='PC 2', color=group, color_discrete_sequence=plot_palette)
    elif components_num == 3:
        fig = px.scatter_3d(trans_df, x='PC 1', y='PC 2', z='PC 3', color=group, color_discrete_sequence=plot_palette)
    
    # todo podmienic opis poniżej na descr="1st Principal Component" if components_num == 1 else "Principal Components"'
    fig_layout(plot_template, fig, chart_titles=chart_titles, plots_colorscale=plot_palette)
    fig.layout.legend.title = 'Group:'
    var_df = pd.DataFrame(model.explained_variance_ratio_,
                          index=trans_df.columns, columns=['ratio of explained variance']
                          )
    
    with cols[0]:
        # Showing PCA chart. FIrst columnt
        st.plotly_chart(fig, use_container_width=True)
        
        # Showing uploaded spectra chart. FIrst columnt
        with st.beta_expander("Uploaded spectra"):
            fig = px.line(df, x=df.index, y=df.columns)
            fig_layout(plot_template, fig, plots_colorscale=plot_palette)

            # What
            # for trace, gr in zip(fig.data, group):
            #     trace['line']['color'] = plot_palette[int(gr)]
            st.plotly_chart(fig, use_container_width=True)
        
        # Showing inversed-transformed spectra chart. FIrst columnt
        with st.beta_expander("Inverse-transformed spectra"):
            reversed_data = model.inverse_transform(trans_df)
            reversed_df = pd.DataFrame(reversed_data, columns=df.index, index=df.columns).T
    
            fig = px.line(reversed_df, x=reversed_df.index, y=reversed_df.columns)
            # todo podmienic opis poniżej na descr=f'Specra recovered from {components_num} PC'
            fig_layout(plot_template, fig, plots_colorscale=plot_palette)
    
            # What
            # for trace, gr in zip(fig.data, group):
            #     trace['line']['color'] = plot_palette[int(gr)]
    
            st.plotly_chart(fig, use_container_width=True)
        
        # Showing PCA details
        with st.beta_expander("Show PCA details"):
            st.table(var_df)
            st.write(trans_df.assign(group=group))
