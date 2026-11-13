import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import multivariate, processing, readers
from vis_helpers import vis_utils, data_customisation, workspace
from vis_helpers.i18n import t, choice


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

    model, scores, loadings, explained = multivariate.pca(data, components_num)

    chart_col, settings_col = st.columns((3, 1))
    with settings_col:
        with st.expander(t('Clustering'), icon=':material/bubble_chart:', expanded=True):
            clustering = st.checkbox(t('Find clusters'), key='pca_cluster',
                                     help=t('Groups spectra by similarity of their PCA scores, without using '
                                            'your group names.'))
            if clustering and len(scores) < 3:
                st.warning(t('Clustering needs at least 3 spectra.'))
            elif clustering:
                method = choice('radio', t('Method'), ['kmeans', 'ward'], key='pca_cluster_method',
                                format_func=lambda m: 'k-means' if m == 'kmeans' else t('Hierarchical (Ward)'))
                auto_k = st.checkbox(t('Number of clusters - automatic'), value=True, key='pca_auto_k',
                                     help=t('Chosen by the best silhouette score.'))
                largest_k = min(8, len(scores) - 1)
                if auto_k:
                    k = None
                elif largest_k > 2:
                    k = st.slider(t('Number of clusters'), 2, largest_k, 2, key='pca_k')
                else:
                    k = 2
                    st.caption(t('Number of clusters') + ': 2')
        with st.expander(t('Chart appearance')):
            settings = vis_utils.chart_settings('pca', titles={
                'x': f'PC 1 ({explained.iloc[0]:.0%})',
                'y': f'PC 2 ({explained.iloc[1]:.0%})' if components_num > 1 else ''})

    clusters = multivariate.cluster(scores, method, k) if clustering and len(scores) > 2 else None

    axes = dict(zip('xyz', scores.columns))
    plot = px.scatter_3d if components_num == 3 else px.scatter
    if clusters:
        # colour = cluster, symbol = the user's group -> both visible at once
        cluster_names = [f'{t("Cluster")} {label}' for label in clusters['labels']]
        group_names_shown = [f'{t("Group")} {g}' for g in group]
        fig = plot(scores, **axes, color=cluster_names, symbol=group_names_shown,
                   color_discrete_sequence=settings['palette'],
                   hover_name=scores.index, labels={'color': t('Cluster'), 'symbol': t('Group')})
    else:
        fig = plot(scores, **axes, color=group, color_discrete_sequence=settings['palette'],
                   hover_name=scores.index, labels={'color': t('Group')})
    fig.update_traces(marker_size=12 if components_num < 3 else 6)

    with chart_col:
        if clusters:
            # results first - with clusters equal to the groups the chart itself barely changes
            table, ari = multivariate.agreement(group, clusters['labels'])
            c = st.columns(3)
            c[0].metric(t('Clusters'), clusters['k'], border=True)
            c[1].metric(t('Silhouette'), '—' if np.isnan(clusters['silhouette']) else f'{clusters["silhouette"]:.2f}',
                        border=True, help=t('Separation of the clusters: close to 1 = well separated, '
                                            'around 0 = overlapping.'))
            if len(set(group)) > 1:
                c[2].metric(t('Agreement with groups (ARI)'), f'{ari:.2f}', border=True,
                            help=t('Adjusted Rand index: 1 = clusters are exactly your groups, ~0 = no relation.'))
            st.caption(t('Number of spectra of each group in each cluster:'))
            table.columns = [f'{t("Cluster")} {c}' for c in table.columns]
            table.index.name = t('Group')
            st.dataframe(table)
            st.caption(t('Chart: colour = cluster found by the algorithm, marker shape = your group.'))

        vis_utils.show_chart(fig, settings, lines=False)

        with st.expander(t('Loadings - which bands differ between samples'), icon=':material/show_chart:'):
            st.caption(t('Large positive or negative values mark the Raman bands that the principal component '
                         'is made of.'))
            loadings_fig = px.line(loadings, color_discrete_sequence=settings['palette'])
            loadings_fig.add_hline(y=0, line_color='#999', line_width=1)
            loadings_settings = vis_utils.default_chart_settings()
            loadings_settings['titles']['y'] = t('Loading')
            vis_utils.show_chart(loadings_fig, loadings_settings)
            top = loadings['PC 1'].abs().nlargest(20)
            peaks_pc1 = sorted({int(round(x / 5) * 5) for x in top.index})[:6]
            st.caption(t('PC 1 is dominated by bands near: {bands} cm⁻¹').format(
                bands=', '.join(str(b) for b in peaks_pc1)))

        with st.expander(t('Scree plot - variance explained by each component'), icon=':material/bar_chart:'):
            variance = multivariate.scree(data)
            scree_fig = go.Figure([
                go.Bar(x=variance.index, y=100 * variance, name=t('Component'),
                       marker_color=vis_utils.sersitive_palette()[1]),
                go.Scatter(x=variance.index, y=100 * variance.cumsum(), name=t('Cumulative'), mode='lines+markers',
                           line=dict(color=vis_utils.sersitive_palette()[0]))])
            scree_settings = vis_utils.default_chart_settings()
            scree_settings['titles'].update({'x': '', 'y': t('Explained variance [%]')})
            scree_fig.update_layout(height=380, hovermode='x unified')
            vis_utils.show_chart(scree_fig, scree_settings, lines=False)

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

    export = scores.assign(group=group)
    if clusters:
        export['cluster'] = clusters['labels']
    vis_utils.download_csv(export, 'pca_scores.csv', t('Download scores (CSV)'), 'pca_csv')
    vis_utils.report_button('pca', lambda: build_report(data, scores, loadings, explained, group, clusters),
                            (tuple(scores.index), tuple(group), components_num, None if not clusters else
                             (clusters['k'], tuple(clusters['labels'])), float(data.to_numpy().sum())))


def build_report(data, scores, loadings, explained, group, clusters):
    from core import report

    rep = report.Report(t('Principal Component Analysis (PCA)'))
    rep.heading(t('Data'))
    counts = pd.Series(group).value_counts()
    rep.key_values({t('Spectra'): len(scores), **{f'{t("Group")} {g}': n for g, n in counts.items()}})
    rep.heading(t('Explained variance ratio'))
    rep.table((100 * explained).round(1).rename('%').to_frame())
    if scores.shape[1] >= 2:
        labels = [f'{t("Cluster")} {c}' for c in clusters['labels']] if clusters else list(group)
        rep.figure(report.scatter_figure(scores.iloc[:, 0], scores.iloc[:, 1],
                                         f'PC 1 ({explained.iloc[0]:.0%})', f'PC 2 ({explained.iloc[1]:.0%})',
                                         groups=labels), width=150)
    if clusters:
        table, ari = multivariate.agreement(group, clusters['labels'])
        table.columns = [f'{t("Cluster")} {c}' for c in table.columns]
        table.index.name = t('Group')
        rep.heading(t('Clustering'))
        rep.key_values({t('Clusters'): clusters['k'], t('Silhouette'): clusters['silhouette'],
                        t('Agreement with groups (ARI)'): ari})
        rep.table(table)
    rep.heading(t('Loadings - which bands differ between samples'))
    rep.figure(report.spectra_figure(loadings, ylabel=t('Loading')))
    return rep.to_bytes()
