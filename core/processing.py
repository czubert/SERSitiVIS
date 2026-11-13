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


#
# # Extended preprocessing (Visualisation page)
#
BASELINE_METHODS = ['modpoly', 'arpls', 'snip']
SMOOTHING_METHODS = ['moving_average', 'savgol']
NORMALIZATION_METHODS = ['minmax', 'max', 'area', 'vector', 'snv', 'peak']


def step_size(index):
    return float(np.median(np.abs(np.diff(np.asarray(index, dtype=float)))))


def remove_spikes(df, threshold=7.0):
    """
    Removes narrow positive spikes (cosmic rays).
    A point is a spike when it sticks out of the 5-point median filtered spectrum by more than threshold x noise
    (noise estimated robustly from point-to-point differences, as in Whitaker & Hayes 2018) AND by more than half
    of the local signal height - so the tops of real, a few points wide Raman peaks are not touched.
    Spike points are replaced by the median filtered values.
    :param threshold: in units of noise SD (lower = more aggressive)
    :return: (cleaned DataFrame, number of replaced points per spectrum)
    """
    from scipy.signal import medfilt

    cleaned = df.astype(float).copy()
    removed = {}
    for col in cleaned.columns:
        y = cleaned[col].to_numpy()
        if len(y) < 10:
            removed[col] = 0
            continue
        smooth_y = medfilt(y, 5)
        residual = y - smooth_y
        # noise level from point-to-point differences (robust, MAD based)
        delta = np.diff(y)
        sigma = 1.4826 * np.median(np.abs(delta - np.median(delta))) / np.sqrt(2)
        if sigma == 0:
            removed[col] = 0
            continue
        z = residual / sigma
        local_floor = pd.Series(smooth_y).rolling(31, min_periods=1, center=True).min().to_numpy()
        spikes = (z > threshold) & (residual > 0.5 * (smooth_y - local_floor))
        spikes = spikes | np.roll(spikes, 1) | np.roll(spikes, -1)  # include the edges of the spike
        spikes[[0, -1]] = False
        y = y.copy()
        y[spikes] = smooth_y[spikes]
        cleaned[col] = y
        removed[col] = int(spikes.sum())
    return cleaned, removed


def baselines(df, method='modpoly', param=5):
    """
    Baseline of every spectrum
    :param method: 'modpoly' (param = polynomial degree), 'arpls' (param = smoothness lambda, e.g. 1e6),
                   'snip' (param = half window in cm-1)
    :param param: one value for all spectra or Dict {column: value}
    :return: DataFrame
    """
    from pybaselines.smooth import snip
    from pybaselines.whittaker import arpls

    result = pd.DataFrame(index=df.index)
    for col in df.columns:
        value = param[col] if isinstance(param, dict) else param
        spectrum = df[col].dropna()
        y = spectrum.to_numpy(dtype=float)
        if method == 'modpoly':
            fitted = baseline(y, int(value), x=spectrum.index)
        elif method == 'arpls':
            fitted = arpls(y, lam=float(value))[0]
        elif method == 'snip':
            half_window = max(1, int(round(float(value) / step_size(spectrum.index))))
            fitted = snip(y, max_half_window=half_window)[0]
        else:
            raise ValueError(f'Unknown baseline method: {method}')
        result[col] = pd.Series(fitted, index=spectrum.index)
    return result


def smooth(df, method='moving_average', window=3):
    """
    :param method: 'moving_average' or 'savgol' (Savitzky-Golay, 2nd order - keeps peak heights better)
    :param window: number of points (made odd for Savitzky-Golay)
    """
    if window <= 1:
        return df
    if method == 'moving_average':
        return df.rolling(window=window, min_periods=1, center=True).mean()
    from scipy.signal import savgol_filter
    window = window + 1 if window % 2 == 0 else window
    result = df.copy()
    for col in df.columns:
        spectrum = df[col].dropna()
        if len(spectrum) > window:
            result.loc[spectrum.index, col] = savgol_filter(spectrum.to_numpy(dtype=float), window, 2)
    return result


def normalize_by(df, method='minmax', peak=None):
    """
    :param method: 'minmax' (0-1), 'max' (max = 1), 'area' (area = 1), 'vector' (Euclidean norm = 1),
                   'snv' (mean 0, SD 1), 'peak' (intensity at the given peak = 1)
    :param peak: (low, high) Raman Shift range of the reference peak for 'peak'
    """
    if method == 'minmax':
        return normalize(df)
    if method == 'max':
        return df / df.max()
    if method == 'area':
        x = df.index.to_numpy(dtype=float)
        return df / pd.Series({col: abs(np.trapezoid(df[col].to_numpy(dtype=float), x)) for col in df.columns})
    if method == 'vector':
        return df / np.sqrt((df ** 2).sum())
    if method == 'snv':
        return (df - df.mean()) / df.std()
    if method == 'peak':
        return df / trim(df, *peak).max()
    raise ValueError(f'Unknown normalization: {method}')


def trim(df, low, high):
    """Keeps Raman Shift range low-high"""
    return df[(df.index >= low) & (df.index <= high)]
