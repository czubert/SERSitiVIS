import pandas as pd
import plotly.express as px
import sklearn.decomposition
import sklearn.preprocessing
import streamlit as st

import processing
from constants import LABELS
from . import sidebar


def main():
    spectra_types = ['EMPTY', 'BWTEK', 'RENI', 'WITEC', 'WASATCH', 'TELEDYNE', 'JOBIN']
    spectrometer = st.sidebar.selectbox("Choose spectra type",
                                        spectra_types,
                                        format_func=LABELS.get,
                                        index=0
                                        )
    sidebar.print_widgets_separator()

    st.write('## PCA Analysis')
    cols = st.beta_columns(2)

    with cols[0]:
        groups_num = st.slider('Number of groups', 1, 6, value=2)
        groups_num = int(groups_num)
        rescale = st.sidebar.checkbox("Rescale")
    with cols[1]:
        components_num = st.slider('Principal components', 1, 3, value=2)
        components_num = int(components_num)

    cols = st.beta_columns(groups_num)
    dfs = []
    for col_ind, col in enumerate(cols):
        with col:
            files = st.file_uploader(label='Upload data',
                                     accept_multiple_files=True,
                                     type=['txt', 'csv'],
                                     key=f'uploader_{col_ind}'
                                     )
            if files:
                df = processing.save_read.files_to_df(files, spectrometer)
                dfs.append(df)

    if len(dfs) < groups_num:
        return

    # TODO a concat nie ma jakiejś opcji, która dba o to, żeby się fajnie concatenowaly dfy z roznymi wartościami X?
    df = pd.concat(dfs, axis=1)
    group = [str(i) for i in range(groups_num) for _ in dfs[i].columns]

    if rescale:
        scaler = sklearn.preprocessing.MinMaxScaler()
        rescaled_data = scaler.fit_transform(df)
        df = pd.DataFrame(rescaled_data, columns=df.columns, index=df.index)

    # TODO może skorzystać z layoutu gotowego? (visualisation.draw.fig_layout)
    fig = px.line(df, x=df.index, y=df.columns, title='Uploaded spectra')
    for trace, gr in zip(fig.data, group):
        trace['line']['color'] = px.colors.qualitative.Plotly[int(gr)]
    fig.layout.legend.title = 'Uploaded file:'

    st.write('## Uploaded Spectra')
    st.plotly_chart(fig, use_container_width=True)

    # TODO pierdzieli się w przypadku kiedy po concat mamy NaN (to co poniżej w TODO),
    # oraz pierdzieli się jak do dwóch róznych grup damy to samo widmo,
    # bo wtedy std jest = 0 dla tyc h2 widm i wywala błąd. masz pomysł jak tego uniknąć?
    model = sklearn.decomposition.PCA(components_num)

    # TODO do wywalenia fillna, trzeba zrobić interpolację
    trans_data = model.fit_transform(df.fillna(0).T)
    trans_df = pd.DataFrame(trans_data, index=df.columns, columns=[f'PC {i}' for i in range(1, components_num + 1)])

    if components_num == 1:
        fig = px.scatter(trans_df, x='PC 1', color=group, title="1st Principal Component")
    elif components_num == 2:
        fig = px.scatter(trans_df, x='PC 1', y='PC 2', color=group, title="Principal Components")
    elif components_num == 3:
        fig = px.scatter_3d(trans_df, x='PC 1', y='PC 2', z='PC 3', color=group, title="Principal Components")

    fig.layout.legend.title = 'Group:'
    var_df = pd.DataFrame(model.explained_variance_ratio_,
                          index=trans_df.columns, columns=['ratio of explained variance']
                          )

    cols = st.beta_columns(2)
    with cols[0]:
        st.plotly_chart(fig, use_container_width=True)
        st.table(var_df)
    with cols[1]:
        st.write('# ')
        st.write('# ')
        st.write(trans_df.assign(group=group))

    with st.beta_expander("Inverse-transformed spectra"):
        reversed_data = model.inverse_transform(trans_df)
        reversed_df = pd.DataFrame(reversed_data, columns=df.index, index=df.columns).T

        fig = px.line(reversed_df, x=reversed_df.index, y=reversed_df.columns,
                      title=f'Specra recovered from {components_num} PC')
        for trace, gr in zip(fig.data, group):
            trace['line']['color'] = px.colors.qualitative.Plotly[int(gr)]

        fig.layout.legend.title = 'Uploaded file:'
        st.plotly_chart(fig, use_container_width=True)
