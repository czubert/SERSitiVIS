"""
PCA, clustering of spectra.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score


def pca(data, n_components):
    """
    :param data: DataFrame, index = Raman Shift, one column per spectrum
    :return: (model, scores DataFrame [spectra x PCs], loadings DataFrame [Raman Shift x PCs],
              explained variance ratio Series)
    """
    model = PCA(n_components)
    names = [f'PC {i}' for i in range(1, n_components + 1)]
    scores = pd.DataFrame(model.fit_transform(data.fillna(0).T), index=data.columns, columns=names)
    loadings = pd.DataFrame(model.components_.T, index=data.index, columns=names)
    explained = pd.Series(model.explained_variance_ratio_, index=names)
    return model, scores, loadings, explained


def scree(data, max_components=10):
    """Explained variance ratio of the first principal components"""
    n = min(max_components, data.shape[1], data.shape[0])
    return pca(data, n)[3]


def cluster(scores, method='kmeans', k=None, max_k=8):
    """
    Groups spectra into clusters (on PCA scores)
    :param method: 'kmeans' or 'ward' (hierarchical)
    :param k: number of clusters, None = chosen automatically by the best silhouette score
    :return: Dict: labels (Series, 1..k), k, silhouette, silhouette_by_k (Series, for auto)
    """
    x = scores.to_numpy()
    n = len(x)

    def fit(n_clusters):
        if method == 'kmeans':
            return KMeans(n_clusters, n_init=10, random_state=0).fit_predict(x)
        return AgglomerativeClustering(n_clusters, linkage='ward').fit_predict(x)

    by_k = pd.Series(dtype=float)
    if k is None:
        for candidate in range(2, min(max_k, n - 1) + 1):
            labels = fit(candidate)
            by_k[candidate] = silhouette_score(x, labels) if len(set(labels)) > 1 else np.nan
        k = int(by_k.idxmax()) if by_k.notna().any() else 2

    k = max(1, min(k, n))
    labels = fit(k) if k > 1 else np.zeros(n, dtype=int)
    silhouette = silhouette_score(x, labels) if 1 < len(set(labels)) < n else np.nan
    # clusters numbered by size (1 = largest), stable between runs
    order = pd.Series(labels).value_counts().index
    renumber = {old: new for new, old in enumerate(order, start=1)}
    labels = pd.Series([renumber[label] for label in labels], index=scores.index)
    return {'labels': labels, 'k': k, 'silhouette': silhouette, 'silhouette_by_k': by_k}


def agreement(groups, clusters):
    """
    How well clusters reproduce the user's groups
    :return: (crosstab DataFrame groups x clusters, adjusted Rand index: 1 = identical, ~0 = random)
    """
    groups = pd.Series(list(groups), index=clusters.index, name='group')
    table = pd.crosstab(groups, clusters.rename('cluster'))
    return table, adjusted_rand_score(groups, clusters)
