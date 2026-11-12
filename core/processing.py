"""
Spectra preprocessing: merging, baseline correction, smoothing, normalisation.
DataFrame convention: index = Raman Shift, one column per spectrum.
"""
import numpy as np
import pandas as pd
from pybaselines.polynomial import modpoly

# ModPoly converges slowly - default tolerance (1e-3) stops too early and leaves baseline
# up to ~15 % of the signal range too high. 1e-5 keeps the error ~3 % at ~4 ms per spectrum.
BASELINE_TOL = 1e-5
BASELINE_MAX_ITER = 5000


def align_spectra(frames):
    """
    Merges DataFrames into one without losing resolution.
    If all spectra share the same Raman Shift values they are simply joined. Otherwise every spectrum is
    linearly interpolated onto the grid of the first one, limited to the range covered by all of them.
    :param frames: List of DataFrames
    :return: DataFrame
    """
    frames = [f[~f.index.duplicated()].sort_index() for f in frames]
    first_index = frames[0].index

    if all(f.index.equals(first_index) for f in frames):
        return pd.concat(frames, axis=1)

    low = max(f.index.min() for f in frames)
    high = min(f.index.max() for f in frames)
    grid = first_index[(first_index >= low) & (first_index <= high)]

    aligned = {}
    for f in frames:
        x = f.index.to_numpy(dtype=float)
        for col in f.columns:
            y = f[col].to_numpy(dtype=float)
            valid = ~np.isnan(y)
            aligned[col] = np.interp(grid, x[valid], y[valid])

    return pd.DataFrame(aligned, index=grid)


def baseline(y, deg, x=None):
    """
    Iterative modified polynomial (ModPoly) baseline, the same algorithm PeakUtils used.
    :param y: array-like, intensities
    :param deg: int, polynomial degree
    :param x: array-like, Raman Shift values (optional, equally spaced points assumed if None)
    :return: ndarray, baseline
    """
    x = None if x is None else np.asarray(x, dtype=float)
    return modpoly(np.asarray(y, dtype=float), x_data=x, poly_order=deg,
                   tol=BASELINE_TOL, max_iter=BASELINE_MAX_ITER)[0]


def subtract_baseline(df, deg):
    """
    Subtracts polynomial baseline from every spectrum (column) of the DataFrame.
    :param df: DataFrame
    :param deg: int, polynomial degree
    :return: DataFrame
    """
    df = df.astype(float)
    for col in df.columns:
        df[col] = df[col] - baseline(df[col], deg, x=df.index)
    return df


def baseline_and_smooth(df, params):
    """
    Baseline correction followed by smoothing (rolling average), each spectrum with its own settings.
    :param df: DataFrame
    :param params: Dict {column: (polynomial degree, smoothing window)}
    :return: (baselines, baseline-corrected, corrected + smoothed) DataFrames
    """
    baselines = pd.DataFrame(index=df.index)
    corrected = pd.DataFrame(index=df.index)
    smoothed = pd.DataFrame(index=df.index)

    for col in df.columns:
        deg, window = params[col]
        spectrum = df[col].dropna()
        baselines[col] = pd.Series(baseline(spectrum, deg, x=spectrum.index), index=spectrum.index)
        corrected[col] = df[col] - baselines[col]
        smoothed[col] = corrected[col].rolling(window=window, min_periods=1, center=True).mean()

    return baselines, corrected, smoothed


def normalize(df):
    """Scales every spectrum to 0-1"""
    return (df - df.min()) / (df.max() - df.min())


def trim(df, low, high):
    """Keeps Raman Shift range low-high"""
    return df[(df.index >= low) & (df.index <= high)]
