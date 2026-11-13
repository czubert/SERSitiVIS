"""
Calibration curve (signal vs concentration) and limit of detection / quantification.

LOD / LOQ:
- from the regression (ICH Q2): LOD = 3.3 * s / slope, LOQ = 10 * s / slope, s = residual standard deviation
- from blank samples (IUPAC): LOD = 3 * s_blank / slope, LOQ = 10 * s_blank / slope
With log10(concentration) on the X axis the limit is the concentration at which the fitted line reaches
mean blank signal + 3 (or 10) * s_blank, so it needs blank spectra.
"""
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.processing import subtract_baseline, trim

MOLAR = {'M': 1, 'mM': 1e-3, 'uM': 1e-6, 'µM': 1e-6, 'nM': 1e-9, 'pM': 1e-12}
MASS = {'ppm': 1, 'ppb': 1e-3, 'ppt': 1e-6}
UNITS = list(MOLAR) + list(MASS)

_UNIT = r'(M|mM|uM|µM|nM|pM|ppm|ppb|ppt)(?![A-Za-z])'
_NUMBER = r'(\d+(?:[.,]\d+)?)'
_PATTERNS = [
    # 5x10-4M, 5×10^-4 M, 2.5*10-6M
    (re.compile(rf'(?<![\d.]){_NUMBER}\s*[x×*]\s*10\^?\s*([-−]\d+)\s*{_UNIT}'), 'mantissa'),
    # 10-3M, 10^-6 M
    (re.compile(rf'(?<![\d.x×*]){"10"}\^?\s*([-−]\d+)\s*{_UNIT}'), 'power'),
    # 1ppm, 0.5 mM, 1e-6M
    (re.compile(rf'(?<![\d.]){_NUMBER}(?:[eE]([-−]?\d+))?\s*{_UNIT}'), 'plain'),
]


def parse_concentration(name):
    """
    Reads the concentration from a file / spectrum name, e.g. 'S09_P_5x10-4M_6sek' -> (5e-4, 'M')
    :return: (value, unit) or None
    """
    for pattern, kind in _PATTERNS:
        match = pattern.search(name)
        if not match:
            continue
        if kind == 'mantissa':
            number, exponent, unit = match.groups()
            value = float(number.replace(',', '.')) * 10 ** int(exponent.replace('−', '-'))
        elif kind == 'power':
            exponent, unit = match.groups()
            value = 10.0 ** int(exponent.replace('−', '-'))
        else:
            number, exponent, unit = match.groups()
            value = float(number.replace(',', '.')) * (10 ** int(exponent.replace('−', '-')) if exponent else 1)
        return value, unit.replace('u', 'µ') if unit == 'uM' else unit
    return None


def convert(value, unit, target):
    """Converts within one family (molar or ppm-like). :return: value in target unit or None"""
    for family in (MOLAR, MASS):
        if unit in family and target in family:
            return value * family[unit] / family[target]
    return None


def concentrations_from_names(names):
    """
    :param names: spectra names
    :return: (Series of concentrations - NaN when not found, most common unit or None)
    """
    parsed = {name: parse_concentration(name) for name in names}
    units = [p[1] for p in parsed.values() if p]
    if not units:
        return pd.Series(np.nan, index=list(names)), None
    unit = max(set(units), key=units.count)
    values = {name: (convert(*p, unit) if p else None) for name, p in parsed.items()}
    return pd.Series(values, dtype=float), unit


def peak_signal(df, low, high, method='height', degree=1):
    """
    Peak signal of every spectrum
    :param df: DataFrame, one column per spectrum
    :param method: 'height' (maximum) or 'area' (integral) after baseline correction
    :param degree: polynomial degree of the baseline fitted within the peak range, None = no correction
    :return: Series
    """
    window = trim(df, low, high)
    if len(window) < 3:
        raise ValueError('Peak range is too narrow')
    if degree is not None:
        window = subtract_baseline(window, degree)
    if method == 'area':
        x = window.index.to_numpy(dtype=float)
        return pd.Series({col: np.trapezoid(window[col].to_numpy(), x) for col in window.columns})
    return window.max()


@dataclass
class CalibrationResult:
    slope: float
    intercept: float
    r2: float
    n: int
    residual_sd: float
    sigma: float  # standard deviation used for LOD/LOQ
    sigma_source: str  # 'regression' or 'blank'
    log_x: bool
    lod: float  # in concentration units, NaN if it cannot be calculated
    loq: float

    def predict(self, concentration):
        x = np.log10(concentration) if self.log_x else np.asarray(concentration, dtype=float)
        return self.slope * x + self.intercept


def fit_calibration(concentration, signal, log_x=False, use_blank=False):
    """
    Linear fit of signal vs concentration (or log10 concentration)
    :param concentration: array-like, one value per spectrum (0 = blank)
    :param signal: array-like, peak signal per spectrum
    :param log_x: Bool, fit against log10(concentration)
    :param use_blank: Bool, LOD/LOQ from the standard deviation of blank (concentration 0) spectra
    :return: CalibrationResult
    """
    c = np.asarray(concentration, dtype=float)
    y = np.asarray(signal, dtype=float)
    valid = ~np.isnan(c) & ~np.isnan(y)
    c, y = c[valid], y[valid]

    blank = y[c == 0]
    points = c > 0 if log_x else np.ones_like(c, dtype=bool)
    x = np.log10(c[points]) if log_x else c[points]
    y_fit = y[points]

    if len(np.unique(x)) < 2:
        raise ValueError('At least two different concentrations are needed')

    slope, intercept = np.polyfit(x, y_fit, 1)
    predicted = slope * x + intercept
    ss_res = float(np.sum((y_fit - predicted) ** 2))
    ss_tot = float(np.sum((y_fit - y_fit.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    residual_sd = np.sqrt(ss_res / (len(x) - 2)) if len(x) > 2 else np.nan

    if use_blank:
        if len(blank) < 2:
            raise ValueError('At least two blank (concentration 0) spectra are needed')
        sigma, source = float(np.std(blank, ddof=1)), 'blank'
    else:
        sigma, source = residual_sd, 'regression'

    if log_x:
        if source == 'blank':
            lod = 10 ** ((blank.mean() + 3 * sigma - intercept) / slope)
            loq = 10 ** ((blank.mean() + 10 * sigma - intercept) / slope)
        else:
            lod = loq = np.nan
    else:
        k = 3 if source == 'blank' else 3.3
        lod, loq = k * sigma / slope, 10 * sigma / slope

    if slope <= 0:  # signal does not grow with concentration - no meaningful detection limit
        lod = loq = np.nan

    return CalibrationResult(slope=float(slope), intercept=float(intercept), r2=r2, n=int(len(x)),
                             residual_sd=residual_sd, sigma=sigma, sigma_source=source, log_x=log_x,
                             lod=float(lod), loq=float(loq))


def summary_by_concentration(concentration, signal):
    """Mean, SD, RSD and number of spectra for every concentration"""
    data = pd.DataFrame({'c': np.asarray(concentration, dtype=float), 'y': np.asarray(signal, dtype=float)})
    table = data.dropna().groupby('c')['y'].agg(['mean', 'std', 'count'])
    table['rsd'] = 100 * table['std'] / table['mean']
    return table
