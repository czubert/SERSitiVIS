"""Substrate background subtraction (core.processing)"""
import numpy as np
import pandas as pd
import pytest

from core import processing


def gauss(x, center, width, height):
    return height * np.exp(-((x - center) / width) ** 2)


X = np.linspace(400, 1800, 1400)
BACKGROUND = gauss(X, 800, 30, 500) + gauss(X, 1350, 60, 300) + 0.2 * X  # substrate bands + slope
ANALYTE = gauss(X, 1075, 8, 2000) + gauss(X, 1585, 10, 3000)


@pytest.mark.parametrize('true_scale', [0.3, 0.7, 1.5])
def test_auto_scale_found_despite_analyte_peaks_and_drift(true_scale):
    rng = np.random.default_rng(0)
    y = true_scale * BACKGROUND + ANALYTE + 100 + 0.05 * X + rng.normal(0, 5, X.size)
    assert processing.background_scale(y, BACKGROUND, X) == pytest.approx(true_scale, rel=0.05)


def test_subtract_background_removes_substrate_bands_keeps_analyte():
    df = pd.DataFrame({'sample': 0.7 * BACKGROUND + ANALYTE}, index=X)
    corrected, factors, _ = processing.subtract_background(df, pd.Series(BACKGROUND, index=X))
    band = (X > 760) & (X < 840)  # substrate band, no analyte there
    assert factors['sample'] == pytest.approx(0.7, rel=0.05)
    assert np.ptp(corrected['sample'][band]) < 0.1 * 500 * 0.7
    assert corrected['sample'].max() == pytest.approx(3000, rel=0.1)


def test_background_on_other_grid_and_shorter_range():
    background = pd.Series(BACKGROUND[::3], index=X[::3])  # coarser grid
    background = background[background.index < 1600]
    df = pd.DataFrame({'a': BACKGROUND + ANALYTE}, index=X)
    corrected, factors, on_grid = processing.subtract_background(df, background, scale=1.0)
    assert corrected.index.max() < 1600 and factors == {'a': 1.0}
    assert len(on_grid) == len(corrected)


def test_background_averaged_from_dataframe():
    background = pd.DataFrame({'b1': BACKGROUND * 0.9, 'b2': BACKGROUND * 1.1}, index=X)
    on_grid = processing.background_on_grid(background, X)
    assert np.allclose(on_grid, BACKGROUND)


def test_background_outside_spectra_range_raises():
    df = pd.DataFrame({'a': ANALYTE}, index=X)
    with pytest.raises(ValueError):
        processing.subtract_background(df, pd.Series([1.0, 2.0], index=[2000.0, 2100.0]))
