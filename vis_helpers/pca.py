import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA
import streamlit as st

from core import processing, readers
from vis_helpers import vis_utils, data_customisation, workspace
from vis_helpers.i18n import t


def main(df):
    """
    :param df: DataFrame with spectra loaded in the sidebar (shared data) or None
    """
    st.header(t('Principal Component Analysis (PCA)'))

    cols = st.columns(2)
    with cols[0]:
        groups_num = int(st.slider(t('Number of groups'), 1, 6, value=2, key='pca_groups'))
    with cols[1]:
        components_num = int(st.slider(t('Principal components'), 1, 3, value=2, key='pca_components'))

    st.info(t('Upload spectra for each group, or choose them from the data loaded in the sidebar.'))

    # every group: its own uploader + optional spectra from the shared data
    group_names, group_frames = [], []
    for i, col in enumerate(st.columns(groups_num)):
        with col.container(border=True):
            group_names.append(st.text_input(t('Group name'), f'{i + 1}', key=f'pca_group_name_{i}'))
            _, uploaded = workspace.stored_uploader(t('Upload spectra'), key=f'pca_files_{i}')
            shared = st.multiselect(t('...or choose from loaded data'), [] if df is None else list(df.columns),
                                    key=f'pca_group_{i}', disabled=df is None)
            frames = [f for f in (uploaded, df[shared] if shared else None) if f is not None]
            group_frames.append(processing.align_spectra(readers.unique_column_names(frames)) if frames else None)

    shared_selected = [s for i in range(groups_num) for s in st.session_state.get(f'pca_group_{i}', [])]
    if len(shared_selected) != len(set(shared_selected)):
        st.warning(t('Each spectrum can belong to one group only'))
        return

    groups = [(name, frame) for name, frame in zip(group_names, group_frames) if frame is not None]
    spectra_count = sum(frame.shape[1] for _, frame in groups)
    if spectra_count < max(2, components_num):
        st.warning(t('Choose at least {n} spectra').format(n=max(2, components_num)))
        return

    data = processing.align_spectra(readers.unique_column_names([frame for _, frame in groups]))
    if data.empty:
        st.error(t('Spectra do not share a common Raman Shift range - upload them separately.'))
        return
    group = [name for name, frame in groups for _ in frame.columns]

    with st.sidebar.expander(t('Processing'), expanded=True):
        if st.checkbox(t('Rescale spectra (0-1)'), key='pca_rescale'):
            data = processing.normalize(data)
        if st.checkbox(t('Baseline correction and smoothing'), key='pca_baseline'):
            deg = data_customisation.choosing_regression_degree('pca')
            window = data_customisation.choosing_smoothening_window('pca')
            _, _, data = processing.baseline_and_smooth(data, {col: (deg, window) for col in data.columns})

    model = PCA(components_num)
    scores = pd.DataFrame(model.fit_transform(data.fillna(0).T), index=data.columns,
                          columns=[f'PC {i}' for i in range(1, components_num + 1)])
    explained = pd.Series(model.explained_variance_ratio_, index=scores.columns)

    chart_col, settings_col = st.columns((3, 1))
    with settings_col.expander(t('Chart appearance')):
        settings = vis_utils.chart_settings('pca', titles={
            'x': f'PC 1 ({explained.iloc[0]:.0%})',
            'y': f'PC 2 ({explained.iloc[1]:.0%})' if components_num > 1 else ''})

    axes = dict(zip('xyz', scores.columns))
    plot = px.scatter_3d if components_num == 3 else px.scatter
    fig = plot(scores, **axes, color=group, color_discrete_sequence=settings['palette'],
               hover_name=scores.index, labels={'color': t('Group')})
    fig.update_traces(marker_size=12 if components_num < 3 else 6)

    with chart_col:
        vis_utils.show_chart(fig, settings, lines=False)

        with st.expander(t('Spectra used')):
            vis_utils.show_chart(px.line(data, color_discrete_sequence=settings['palette']),
                                 vis_utils.default_chart_settings())

        with st.expander(t('Spectra recovered from principal components')):
            recovered = pd.DataFrame(model.inverse_transform(scores), index=data.columns, columns=data.index).T
            vis_utils.show_chart(px.line(recovered, color_discrete_sequence=settings['palette']),
                                 vis_utils.default_chart_settings())

        with st.expander(t('Details')):
            st.dataframe(explained.rename(t('Explained variance ratio')).to_frame().style.format('{:.1%}'))
            st.dataframe(scores.assign(**{t('Group'): group}))

    vis_utils.download_csv(scores.assign(group=group), 'pca_scores.csv', t('Download scores (CSV)'), 'pca_csv')
