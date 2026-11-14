"""
Calculations: Relative Standard Deviation (RSD) and Enhancement Factor (EF).
"""
import numpy as np
import pandas as pd

from core.processing import SNIP_HALF_WINDOW, baseline, baselines, trim

AVOGADRO = 6.02214076e23  # [1/mol]


#
# # RSD
#
def rsd_stats(values):
    """
    :param values: Series, one value per spectrum
    :return: (mean, standard deviation, RSD as a fraction)
    """
    mean, std = values.mean(), values.std()
    return mean, std, std / mean


def peak_window(df, low, high, mode='snip', half_window=SNIP_HALF_WINDOW):
    """
    Peak range of every spectrum and the baseline under it
    :param mode: 'snip' - SNIP baseline of the whole spectrum, 'line' - straight line fitted in the peak range only,
                 'none' - zero (absolute intensities)
    :return: (DataFrame of the peak range, DataFrame of the baseline on the same points)
    """
    window = trim(df, low, high)
    if mode == 'snip':
        return window, trim(baselines(df, 'snip', half_window), low, high)
    if mode == 'line':
        return window, window.apply(lambda y: baseline(y, 1, x=window.index))
    return window, window * 0.0


def peak_heights(df, peak1, peak2=None, mode='snip', half_window=SNIP_HALF_WINDOW):
    """
    Peak height above the baseline in every spectrum (or the peak1 / peak2 ratio)
    :param peak1, peak2: (low, high) Raman Shift ranges
    :return: Series {spectrum: value}
    """
    def height(peak):
        window, base = peak_window(df, *peak, mode, half_window)
        return (window - base).max()

    return height(peak1) if peak2 is None else height(peak1) / height(peak2)


def rsd_confidence_interval(rsd, n, level=0.95):
    """
    Confidence interval of RSD measured from n spectra (Vangel 1996 - accurate also for RSD of tens of %).
    Example: RSD 10 % from 5 spectra -> 6.0-29 %, from 20 spectra -> 7.6-14.6 %.
    :param rsd: measured RSD as a fraction
    :return: (low, high) as fractions; high = inf when n is too small to limit it
    """
    from scipy.stats import chi2

    if n < 2 or not np.isfinite(rsd) or rsd < 0:
        return np.nan, np.nan
    dof = n - 1

    def bound(u):
        denominator = ((u + 2) / n - 1) * rsd ** 2 + u / dof
        return rsd / np.sqrt(denominator) if denominator > 0 else np.inf

    return bound(chi2.ppf(1 - (1 - level) / 2, dof)), bound(chi2.ppf((1 - level) / 2, dof))


def rsd_table(values):
    """
    :param values: Dict {label: Series of peak heights (or ratios), one value per spectrum}
    :return: DataFrame: mean, SD and RSD [%] for every label
    """
    results = {}
    for label, series in values.items():
        mean, std, rsd = rsd_stats(series)
        low, high = rsd_confidence_interval(rsd, series.count())
        results[label] = {'Mean': mean, 'Standard deviation': std, 'RSD[%]': rsd * 100,
                          'RSD 95 % CI from [%]': low * 100, 'RSD 95 % CI to [%]': high * 100}

    return pd.DataFrame(results)


#
# # Enhancement Factor
# Method: 'Enhancement Factor (EF): teoria i praktyka', IChF PAN 2020
#
def num_of_molecules(conc, vol):
    """
    Number of molecules in the solution
    :param conc: Float, concentration [mol/dm^3]
    :param vol: Float, volume [ml]
    :return: Float
    """
    return AVOGADRO * conc * vol * 10 ** (-3)


def laser_spot_diameter(wave_length_nm, numerical_aperture):
    """
    :param wave_length_nm: laser wavelength [nm]
    :param numerical_aperture: lens numerical aperture
    :return: Float, diameter of the laser spot [m]
    """
    return 1.22 * wave_length_nm * 10 ** (-9) / numerical_aperture


def laser_spot_area(spot_diameter):
    """:return: Float, area of the laser spot [m^2]"""
    return np.pi * (spot_diameter / 2) ** 2


def n_sers(num_molecules, spot_area, coverage, platform_area):
    """
    Number of molecules within the laser spot on the SERS platform
    :param platform_area: [m^2], including surface development coefficient
    """
    return num_molecules * spot_area * coverage / platform_area


def n_raman(spot_area, penetration_depth, density, molecular_weight):
    """
    Number of molecules of the solid compound irradiated during Raman measurement
    :param spot_area: [m^2]
    :param penetration_depth: [m]
    :param density: [g/cm^3]
    :param molecular_weight: [g/mol]
    """
    volume = spot_area * penetration_depth  # [m^3]
    mass = volume * density * 10 ** 6  # [g]
    return mass / molecular_weight * AVOGADRO


def enhancement_factor(i_sers, n_sers_, i_raman, n_raman_):
    return (i_sers / n_sers_) * (n_raman_ / i_raman)


def peak_intensity(df, low, high):
    """
    Peak intensity read from the mean spectrum
    :param df: DataFrame, one column per spectrum
    :return: Dict: intensity, position, n spectra, SD of per-spectrum peak intensities (None for one spectrum)
    """
    mask = (df.index >= low) & (df.index <= high)
    if not mask.any():
        return None
    mean_peak = df[mask].mean(axis=1)
    per_spectrum = df[mask].max()
    return {'intensity': mean_peak.max(),
            'position': mean_peak.idxmax(),
            'n': df.shape[1],
            'sd': per_spectrum.std() if df.shape[1] > 1 else None,
            'rsd': per_spectrum.std() / per_spectrum.mean() if df.shape[1] > 1 else None}


def ef_from_parameters(p):
    """
    EF from all inputs (works with numbers and numpy arrays - used for Monte Carlo)
    :param p: Dict with keys: concentration [mol/dm3], volume [ml], wavelength [nm], aperture, size_x, size_y [mm],
              development, coverage, depth [m], density [g/cm3], molecular_weight [g/mol], i_sers, i_raman
    """
    n = num_of_molecules(p['concentration'], p['volume'])
    s0 = laser_spot_area(laser_spot_diameter(p['wavelength'], p['aperture']))
    platform = p['size_x'] * p['size_y'] * 10 ** (-6) * p['development']
    return enhancement_factor(p['i_sers'], n_sers(n, s0, p['coverage'], platform),
                              p['i_raman'], n_raman(s0, p['depth'], p['density'], p['molecular_weight']))


def ef_uncertainty(parameters, ranges, relative_sd, draws=20000, seed=0):
    """
    Monte Carlo uncertainty of EF
    :param parameters: Dict of nominal values (see ef_from_parameters)
    :param ranges: Dict {parameter: (low, high)} - uniform distribution within the range
    :param relative_sd: Dict {parameter: relative SD} - normal distribution (e.g. intensities)
    :return: Dict: median, low (5th percentile), high (95th percentile),
             sensitivity {parameter: (EF at low end, EF at high end)}
    """
    rng = np.random.default_rng(seed)
    sample = {key: np.full(draws, float(value)) for key, value in parameters.items()}
    for key, (low, high) in ranges.items():
        sample[key] = rng.uniform(low, high, draws)
    for key, sd in relative_sd.items():
        sample[key] = parameters[key] * np.clip(rng.normal(1, sd, draws), 0.05, None)
    values = ef_from_parameters(sample)

    sensitivity = {}
    for key, (low, high) in ranges.items():
        sensitivity[key] = (ef_from_parameters({**parameters, key: low}), ef_from_parameters({**parameters, key: high}))
    for key, sd in relative_sd.items():
        sensitivity[key] = (ef_from_parameters({**parameters, key: parameters[key] * (1 - sd)}),
                            ef_from_parameters({**parameters, key: parameters[key] * (1 + sd)}))

    low, median, high = np.percentile(values, [5, 50, 95])
    return {'median': median, 'low': low, 'high': high, 'sensitivity': sensitivity}


def analytical_ef(i_sers, c_sers, i_raman, c_raman):
    """
    Analytical enhancement factor: AEF = (I_SERS / c_SERS) / (I_Raman / c_Raman)
    c_SERS, c_Raman - analyte concentrations in the SERS and in the normal Raman measurement (same units)
    """
    return (i_sers / c_sers) / (i_raman / c_raman)
