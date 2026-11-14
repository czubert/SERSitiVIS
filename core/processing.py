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
# SNIP half window [cm-1]: about 2x the FWHM of the measured bands. Tested on synthetic p-MBA-like spectra with known
# peak heights (bands 1075 / 1590 cm-1, FWHM 16 / 20): 30-50 cm-1 measures them within a few %, 60 overestimated the
# 1075 band by 15 % (fluorescence left under it) and 10-20 cut into the peaks. Real p-MBA spectra (532, 633, 785 nm):
# peak heights stop changing from 30-40 cm-1 on.
SNIP_HALF_WINDOW = 40
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


# Substrate background subtraction.
# The background (blank substrate spectrum) is scaled, because intensity changes with focus, laser power and
# substrate spot. Automatic scale: the spectrum is fitted as  scale * background + low-order polynomial
# (fluorescence, drift). Analyte peaks would inflate the scale, so points sticking out above the fit by more than
# BACKGROUND_OUTLIER x noise (robust SD of the residuals) are left out and the fit repeated until the set of points
# does not change. Substrate bands fit well at the right scale and stay in. The polynomial is not subtracted -
# that is the job of baseline correction.
BACKGROUND_POLY_ORDER = 2
BACKGROUND_OUTLIER = 3.0
BACKGROUND_MAX_ITER = 100


def background_on_grid(background, index):
    """
    :param background: Series (index = Raman Shift) or DataFrame (averaged over columns)
    :param index: target Raman Shift values
    :return: Series on index, NaN outside the background range
    """
    if isinstance(background, pd.DataFrame):
        background = background.mean(axis=1)
    background = background.dropna().sort_index()
    background = background[~background.index.duplicated()]
    x = np.asarray(index, dtype=float)
    values = np.interp(x, background.index.to_numpy(dtype=float), background.to_numpy(dtype=float),
                       left=np.nan, right=np.nan)
    return pd.Series(values, index=index)


def background_scale(y, background, x=None, poly_order=BACKGROUND_POLY_ORDER):
    """
    Automatic scale factor of the background in spectrum y (see the comment above)
    :param y: intensities, background: background on the same points, x: Raman Shift
    :return: float >= 0
    """
    y = np.asarray(y, dtype=float)
    background = np.asarray(background, dtype=float)
    x = np.arange(len(y), dtype=float) if x is None else np.asarray(x, dtype=float)
    span = x.max() - x.min()
    xs = (x - x.min()) / span * 2 - 1 if span else np.zeros_like(x)
    design = np.column_stack([background] + [xs ** p for p in range(poly_order + 1)])

    used = np.ones(len(y), dtype=bool)
    for _ in range(BACKGROUND_MAX_ITER):
        coef = np.linalg.lstsq(design[used], y[used], rcond=None)[0]
        residuals = y - design @ coef
        noise = 1.4826 * np.median(np.abs(residuals[used] - np.median(residuals[used])))
        new_used = residuals <= BACKGROUND_OUTLIER * max(noise, 1e-12 * (np.ptp(y) or 1))
        if new_used.sum() < design.shape[1] + 2 or np.array_equal(new_used, used):
            break
        used = new_used
    return max(float(coef[0]), 0.0)


def subtract_background(df, background, scale='auto'):
    """
    Subtracts the substrate background from every spectrum
    :param df: DataFrame of spectra
    :param background: Series or DataFrame (averaged) with the background spectrum, any Raman Shift grid
    :param scale: 'auto' (fitted for every spectrum) or a number (the same factor for all)
    :return: (DataFrame limited to the range covered by the background, Dict {column: scale},
              Series - background on the grid of the result)
    """
    on_grid = background_on_grid(background, df.index)
    covered = on_grid.notna().to_numpy()
    df, on_grid = df[covered], on_grid[covered]
    if len(df) < 3:
        raise ValueError('Background does not cover the spectra')

    result, factors = df.copy(), {}
    x = df.index.to_numpy(dtype=float)
    for col in df.columns:
        spectrum = df[col]
        valid = spectrum.notna().to_numpy()
        if scale == 'auto':
            factors[col] = background_scale(spectrum[valid], on_grid[valid], x[valid]) if valid.sum() > 5 else 0.0
        else:
            factors[col] = float(scale)
        result[col] = spectrum - factors[col] * on_grid
    return result, factors, on_grid
