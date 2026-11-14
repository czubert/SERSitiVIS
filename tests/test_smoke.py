"""
Smoke tests: example files are read correctly and every app view works on example data.
Run from the project root:  python -m pytest
"""
import glob
import os

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from core import readers, processing
from vis_helpers import workspace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_FORMAT = {'bwtek': 'BWTEK', 'wasatch': 'WASATCH', 'renishaw': 'TABLE', 'witec': 'TABLE',
                   'teledyne': 'TABLE', 'jobin_yvon': 'TABLE'}
EXAMPLES = sorted(glob.glob(os.path.join(ROOT, 'data', 'data_examples', '**', '*.*'), recursive=True))


@pytest.fixture(autouse=True)
def run_from_root(monkeypatch):
    monkeypatch.chdir(ROOT)


def read(path, file_format='AUTO'):
    with open(path, 'rb') as f:
        return readers.read_file(os.path.basename(path), f.read(), file_format)


def folder(path):
    return os.path.relpath(path, os.path.join(ROOT, 'data', 'data_examples')).split(os.sep)[0]


#
# # Reading files
#
@pytest.mark.parametrize('path', EXAMPLES, ids=[os.path.basename(p) for p in EXAMPLES])
def test_example_file_detected_and_read(path):
    loaded = read(path)
    assert loaded.format == EXPECTED_FORMAT[folder(path)]
    df = loaded.data
    assert len(df) > 500
    assert all(dtype.kind == 'f' for dtype in df.dtypes)
    assert df.index.is_monotonic_increasing and not df.index.duplicated().any()
    assert df.notna().all().all()


@pytest.mark.parametrize('instrument', workspace.EXAMPLES)
def test_example_sets_merge(instrument):
    df, loaded, errors = readers.read_files(workspace.example_files(instrument))
    assert not errors
    assert df.shape[1] >= 2 and df.notna().all().all()


def test_files_from_different_spectrometers_merge():
    files = workspace.example_files('BWTEK')[:1] + workspace.example_files('Renishaw')[:1]
    df, loaded, errors = readers.read_files(files)
    assert [f.format for f in loaded] == ['BWTEK', 'TABLE']
    assert df.shape[1] == 2 and len(df) > 100 and df.notna().all().all()


def test_same_file_twice_keeps_both():
    files = workspace.example_files('Renishaw')[:1] * 2
    df, _, _ = readers.read_files(files)
    assert list(df.columns) == ['renishaw(5)', 'renishaw(5) (2)']


def test_witec_file_with_two_raman_shift_columns():
    df = read(os.path.join(ROOT, 'data', 'data_examples', 'witec', 'WITec(5).csv')).data
    assert list(df.columns) == ['WITec(5) (mM)', 'WITec(5) (uM)']


def test_non_utf8_file():
    with open(os.path.join(ROOT, 'data', 'data_examples', 'renishaw', 'renishaw(5).txt'), 'rb') as f:
        content = '# próbka żółć\n'.encode('cp1250') + f.read()
    assert not readers.read_file('cp1250.txt', content).data.empty


def test_semicolon_and_decimal_comma():
    text = 'Raman Shift;Intensity\n' + '\n'.join(f'{x},5;{x * 10},25' for x in range(500, 700))
    df = readers.read_file('pl.txt', text).data
    assert df.index[0] == 500.5 and df.iloc[0, 0] == 5000.25


def test_unreadable_file_reports_error():
    df, loaded, errors = readers.read_files([('notes.txt', b'just some text\nno numbers here\n')])
    assert df is None and 'notes.txt' in errors


#
# # Processing
#
def test_baseline_recovers_background_under_peaks():
    x = np.linspace(400, 1800, 1500)
    background = 2000 + 1.5 * (x - 400) - 6e-4 * (x - 400) ** 2
    peaks = sum(h * np.exp(-((x - c) / 6) ** 2) for c, h in [(640, 3000), (1080, 20000), (1590, 15000)])
    estimated = processing.baseline(background + peaks, 2, x=x)
    assert np.max(np.abs(estimated - background)) / np.ptp(peaks) < 0.01


#
# # App
#
PAGES = {'start': 'app_pages/start.py', 'visualisation': 'app_pages/visualisation.py', 'rsd': 'app_pages/rsd.py',
         'ef': 'app_pages/enhancement_factor.py', 'pca': 'app_pages/pca.py',
         'calibration': 'app_pages/calibration.py', 'maps': 'app_pages/maps.py'}


def new_app(example=None, page=None, language=None):
    app = AppTest.from_file(os.path.join(ROOT, 'vis.py'), default_timeout=60)
    if language:
        app.session_state['lang'] = language
    app.run()
    if example:
        app.selectbox(key='workspace_example').set_value(example).run()
    if page:
        app.switch_page(PAGES[page]).run()
    return app


@pytest.mark.parametrize('language', ['en', 'pl', 'de', 'uk'])
@pytest.mark.parametrize('page', PAGES)
def test_page_renders(page, language):
    assert not new_app(page=page, language=language).exception
    assert not new_app('Jobin Yvon T64000', page, language).exception


def test_example_button_on_start_page():
    app = new_app()
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state['_ws_example'] == workspace.DEFAULT_EXAMPLE
    assert app.get('plotly_chart')


def test_data_survives_page_changes():
    app = new_app('Renishaw', 'rsd')
    for page in ['pca', 'ef', 'start', 'visualisation']:
        app.switch_page(PAGES[page]).run()
    assert app.selectbox(key='workspace_example').value == 'Renishaw'
    assert app.get('plotly_chart')


@pytest.mark.parametrize('chart', ['SINGLE', 'MS', 'GS', 'P3D'])
@pytest.mark.parametrize('processed', [False, True])
@pytest.mark.parametrize('instrument', workspace.EXAMPLES)
def test_visualisation(instrument, chart, processed):
    app = new_app(instrument, 'visualisation')
    app.radio(key='chart_type').set_value(chart).run()
    if processed:
        app.checkbox(key='processed').check().run()
        app.selectbox(key='normalization').set_value('minmax').run()
        if chart in {'SINGLE', 'MS'}:
            app.checkbox(key='show_steps').check().run()
    else:
        app.slider(key='range').set_value((800, 1500)).run()
    assert not app.exception
    assert app.get('plotly_chart')


@pytest.mark.parametrize('instrument', workspace.EXAMPLES)
def test_pca(instrument):
    app = new_app(instrument, 'pca')
    names = app.multiselect(key='pca_group_0').options
    app.multiselect(key='pca_group_0').set_value(names[:1]).run()
    app.multiselect(key='pca_group_1').set_value(names[1:]).run()
    assert not app.exception
    assert app.get('plotly_chart')


def test_pca_same_spectrum_in_two_groups():
    app = new_app('Jobin Yvon T64000', 'pca')
    names = app.multiselect(key='pca_group_0').options
    app.multiselect(key='pca_group_0').set_value(names).run()
    app.multiselect(key='pca_group_1').set_value(names[:1]).run()
    assert not app.exception and app.warning


@pytest.mark.parametrize('instrument', workspace.EXAMPLES)
def test_rsd(instrument):
    app = new_app(instrument, 'rsd')
    app.radio(key='rsd_type').set_value('P2P').run()
    assert not app.exception
    assert app.table


def test_chart_selection_to_range():
    from vis_helpers.vis_utils import selected_range
    assert selected_range({'selection': {'box': [{'x': [1100.4, 1050.2], 'y': [0, 1]}], 'points': []}})         == (1050.2, 1100.4)
    assert selected_range({'selection': {'box': [], 'points': [{'x': 900}, {'x': 950}]}}) == (900, 950)
    assert selected_range({'selection': {'box': [], 'points': []}}) is None


def test_ef_from_spectra():
    app = AppTest.from_file(os.path.join(ROOT, 'vis.py'), default_timeout=60)
    app.session_state['_ef_source'] = 'spectra'
    app.run()
    app.selectbox(key='workspace_example').set_value('Jobin Yvon T64000').run()
    app.switch_page(PAGES['ef']).run()
    names = app.multiselect(key='ef_Raman_spectra').options
    app.multiselect(key='ef_Raman_spectra').set_value(names[:1]).run()
    app.multiselect(key='ef_SERS_spectra').set_value(names[1:]).run()
    app.slider(key='ef_Raman_range').set_value((1070, 1090)).run()
    app.slider(key='ef_SERS_range').set_value((1070, 1090)).run()
    assert not app.exception
    assert any(m.label == 'EF' for m in app.metric)


def test_ef_matches_publication_example():
    """Values from 'Enhancement Factor (EF): teoria i praktyka', IChF PAN 2020, section 4.3 -> EF = 6.1e7"""
    app = new_app(page='ef')
    inputs = {'ef_conc_x': 1, 'ef_conc_n': -6, 'ef_volume': 2000.0, 'ef_wavelength': 785, 'ef_na': 0.40,
              'ef_size_x': 3.0, 'ef_size_y': 3.0, 'ef_development': 2.0, 'ef_coverage': 0.1, 'ef_depth': 2.0,
              'ef_density': 1.3, 'ef_molecular_weight': 154.19, 'ef_i_raman': 1000, 'ef_i_sers': 40000}
    for key, value in inputs.items():
        app.number_input(key=key).set_value(value)
    app.run()
    assert not app.exception
    assert next(m for m in app.metric if m.label == 'EF').value == '6.1e+07'


def test_rsd_not_affected_by_chart_normalisation():
    """Normalising each spectrum to its maximum made RSD of the strongest peak 0 %"""
    app = new_app('Jobin Yvon T64000', 'rsd')
    before = app.table[0].value.astype(float)
    assert before.loc['RSD[%]', 'RAW data'] > 1
    app.checkbox(key='rsd_normalize').check().run()
    assert app.table[0].value.astype(float).equals(before)


def test_rsd_snip_half_window_changes_result():
    app = new_app('Jobin Yvon T64000', 'rsd')
    app.slider(key='rsd_Peak 1_range').set_value((1050, 1110)).run()
    results = []
    for half_window in (15, 200):
        app.slider(key='rsd_half_window').set_value(half_window).run()
        results.append(app.table[0].value.astype(float).loc['RSD[%]', 'Baseline corrected'])
    assert not app.exception and results[0] != results[1]


def test_default_snip_half_window_measures_peak_heights():
    """Default half window measures p-MBA-like bands (FWHM 16-20 cm-1) on strong fluorescence within 7 %"""
    from core.processing import baselines, trim
    from vis_helpers.data_customisation import SNIP_HALF_WINDOW
    x = np.arange(400, 1800, 1.5)
    peaks = {1077: (10000, 16), 1588: (15000, 20)}
    analyte = sum(h / (1 + ((x - c) / (w / 2)) ** 2) for c, (h, w) in peaks.items())
    fluorescence = 30000 * np.exp(-((x - 1200) / 700) ** 2) + 4000 + 1.5 * (x - 1100)
    df = pd.DataFrame({'s': analyte + fluorescence}, index=x)
    corrected = df - baselines(df, 'snip', SNIP_HALF_WINDOW)
    for center, (height, _) in peaks.items():
        assert abs(trim(corrected, center - 15, center + 15)['s'].max() / height - 1) < 0.07


#
# # Translations
#
def translated_texts():
    """All string literals passed to t() in the app code"""
    import ast
    texts = set()
    for path in glob.glob(os.path.join(ROOT, 'vis_helpers', '*.py')) + [os.path.join(ROOT, 'vis.py')]:
        with open(path, encoding='utf-8') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 't' and node.args                     and isinstance(node.args[0], ast.Constant):
                texts.add(node.args[0].value)
    return texts


@pytest.mark.parametrize('language', ['pl', 'de', 'uk'])
def test_every_text_has_translation(language):
    from vis_helpers.i18n import translations
    missing = sorted(text for text in translated_texts() if text not in translations()[language])
    assert not missing, missing


@pytest.mark.parametrize('page', PAGES)
def test_language_switch_keeps_choices(page):
    app = new_app('Renishaw', 'visualisation')
    app.radio(key='chart_type').set_value('MS').run()
    app.switch_page(PAGES[page]).run()
    app.radio(key='_lang_widget').set_value('pl').run()
    assert not app.exception
    app.switch_page(PAGES['visualisation']).run()
    assert not app.exception
    assert app.radio(key='chart_type__pl').value == 'MS'
    assert app.session_state['_ws_example'] == 'Renishaw'
    app.radio(key='_lang_widget').set_value('en').run()
    assert not app.exception and app.radio(key='chart_type').value == 'MS'


#
# # Calibration
#
@pytest.mark.parametrize('name,expected', [
    ('!P S09.090_P_5x10-4M_6sek_20%_2', (5e-4, 'M')),
    ('!pizo S10.019_Pizo_10-3M_6sek_20%_2', (1e-3, 'M')),
    ('SERSitive_next_day_1ppm', (1.0, 'ppm')),
    ('R6G 2,5x10^-6 M', (2.5e-6, 'M')),
    ('pMBA 0.5 mM', (0.5, 'mM')),
    ('blank_0M', (0.0, 'M')),
    ('4MPBA_9B22_10s_1x', None),
    ('S23.085_PMBA_10sek_3acc_0.2mW_633nm', None),
])
def test_concentration_from_name(name, expected):
    from core.calibration import parse_concentration
    result = parse_concentration(name)
    if expected is None:
        assert result is None
    else:
        assert result[1] == expected[1] and np.isclose(result[0], expected[0])


def test_calibration_fit_and_lod():
    from core.calibration import fit_calibration
    c = np.repeat([0.0, 1, 2, 4, 8], 3)
    noise = np.tile([-5.0, 0, 5], 5)  # SD of every level = 5
    y = 100 * c + 50 + noise
    result = fit_calibration(c, y)
    assert np.isclose(result.slope, 100) and np.isclose(result.intercept, 50) and result.r2 > 0.999
    assert np.isclose(result.lod, 3.3 * result.residual_sd / 100)
    blank = fit_calibration(c, y, use_blank=True)
    assert np.isclose(blank.lod, 3 * 5 / 100) and np.isclose(blank.loq, 10 * 5 / 100)
    log_blank = fit_calibration(c, y, log_x=True, use_blank=True)
    assert log_blank.lod > 0
    decreasing = fit_calibration(c, 1000 - y)
    assert np.isnan(decreasing.lod) and np.isnan(decreasing.loq)


def test_peak_signal_height_and_area():
    from core.calibration import peak_signal
    x = np.linspace(1000, 1200, 401)
    peak = 1000 * np.exp(-((x - 1100) / 5) ** 2)
    df = pd.DataFrame({'a': peak + 200, 'b': 2 * peak + 300}, index=x)
    height = peak_signal(df, 1050, 1150)
    assert np.allclose(height, [1000, 2000], rtol=0.01)
    area = peak_signal(df, 1050, 1150, method='area')
    assert np.isclose(area['b'] / area['a'], 2, rtol=0.01)


def test_convenient_unit():
    from core.calibration import concentrations_from_names
    values, unit = concentrations_from_names(['R6G_1x10-6M_1', 'R6G_10x10-6M_1', 'blank_0M'])
    assert unit == 'µM' and list(values) == [1.0, 10.0, 0.0]
    assert concentrations_from_names(['a_1ppm', 'b_2ppm'])[1] == 'ppm'


def test_calibration_page():
    app = new_app('Wasatch', 'calibration')
    assert not app.exception
    assert [m.label for m in app.metric][:3] == ['LOD', 'LOQ', 'R²']  # peak chosen automatically
    app.selectbox(key='cal_unit').set_value('ppb').run()
    assert not app.exception
    app.slider(key='cal_range').set_value((990, 1110)).run()
    assert not app.exception
    labels = [m.label for m in app.metric]
    assert labels[:3] == ['LOD', 'LOQ', 'R²']


#
# # EF parameters file
#
def test_ef_parameters_file_new_format():
    from vis_helpers.enhancement_factor import parse_parameters
    csv = ('key,parameter,value,unit\nef_conc_x,conc_x,2,x\nef_conc_n,conc_n,-6,n\nef_volume,volume,1500.0,µl\n'
           'ef_wavelength,wavelength,633,nm\nef_na,na,0.4,NA\nef_i_sers,i_sers,40000,a.u.\n'
           'result_7,EF,6.1e7,\nef_depth,depth,99,mm\n').encode('utf-8')
    loaded, skipped = parse_parameters(csv)
    assert loaded == {'ef_conc_x': 2, 'ef_conc_n': -6, 'ef_volume': 1500.0, 'ef_wavelength': 633, 'ef_na': 0.4,
                      'ef_i_sers': 40000}
    assert skipped == ['ef_depth']  # 99 mm is out of range
    assert isinstance(loaded['ef_wavelength'], int) and isinstance(loaded['ef_volume'], float)


def test_ef_parameters_file_previous_format():
    from vis_helpers.enhancement_factor import parse_parameters
    csv = ('Parameter,Value\nC [mol/dm³],5e-06\nV [ml],2.0\nλ [nm],785\nNA,0.22\nS platform [m²],4e-05\n'
           'coverage,0.1\nd [g/cm³],1.3\nM [g/mol],154.19\nh [m],0.002\nI Raman,1000\nI SERS,60000\n').encode('utf-8')
    loaded, _ = parse_parameters(csv)
    assert loaded['ef_conc_x'] == 5 and loaded['ef_conc_n'] == -6
    assert loaded['ef_volume'] == 2000.0 and loaded['ef_depth'] == 2.0 and loaded['ef_wavelength'] == 785


def test_ef_parameters_file_rejects_other_files():
    from vis_helpers.enhancement_factor import parse_parameters
    loaded, _ = parse_parameters('a,b\n1,2\n'.encode('utf-8'))
    assert loaded == {}


#
# # Peaks
#
def test_peaks_found_at_known_positions():
    from core.peaks import find_peaks
    x = np.arange(400, 1800, 0.5)
    known = [(520, 3000, 8), (1075, 20000, 12), (1588, 15000, 10)]
    y = 1000 + sum(h * np.exp(-4 * np.log(2) * ((x - c) / w) ** 2) for c, h, w in known)
    y += np.random.default_rng(0).normal(0, 50, x.size)
    peaks = find_peaks(pd.Series(y, index=x))
    assert len(peaks) == 3
    assert np.allclose(peaks['position'], [c for c, _, _ in known], atol=1)
    assert np.allclose(peaks['fwhm'], [w for _, _, w in known], atol=0.5)
    assert len(find_peaks(pd.Series(y, index=x), max_peaks=1)) == 1


@pytest.mark.parametrize('chart', ['SINGLE', 'MS', 'GS'])
@pytest.mark.parametrize('instrument', workspace.EXAMPLES)
def test_visualisation_peaks(instrument, chart):
    app = new_app(instrument, 'visualisation')
    app.radio(key='chart_type').set_value(chart).run()
    app.checkbox(key='peaks').check().run()
    if chart == 'GS':
        app.slider(key='shift').set_value(0.3).run()
    else:
        app.checkbox(key='processed').check().run()
        app.checkbox(key='show_steps').check().run()
    assert not app.exception
    assert len(app.dataframe) >= 1


def test_shared_peaks_labelled_once():
    from core.peaks import label_once
    table = pd.DataFrame({'spectrum': ['a', 'b', 'a', 'b'], 'position': [1000.0, 1001.5, 1200.0, 1300.0],
                          'intensity': [5.0, 9.0, 3.0, 4.0]})
    assert list(label_once(table, tolerance=5)) == [False, True, True, True]


#
# # Maps
#
def synthetic_map_file(nx=4, ny=3):
    """Renishaw-like map export: X, Y, Wave (descending), Intensity"""
    shift = np.arange(1800, 400, -2.0)
    lines = ['#X\t#Y\t#Wave\t#Intensity']
    for j in range(ny):
        for i in range(nx):
            gain = 1 + 0.1 * i + 0.05 * j
            intensity = 1000 + 5000 * gain * np.exp(-((shift - 1075) / 8) ** 2)
            lines += [f'{10 * i}\t{10 * j}\t{s:.1f}\t{v:.2f}' for s, v in zip(shift, intensity)]
    return ('\n'.join(lines) + '\n').encode()


def test_map_file_read_with_coordinates():
    from core import maps
    df, loaded, errors = readers.read_files([('map.txt', synthetic_map_file())])
    assert not errors and loaded[0].format == 'MAP' and df.shape[1] == 12
    coords = maps.coordinates_from_names(df.columns)
    assert sorted(coords['x'].unique()) == [0, 10, 20, 30] and sorted(coords['y'].unique()) == [0, 10, 20]


def test_map_uniformity_and_grid():
    from core import maps
    from core.calibration import peak_signal
    df, _, _ = readers.read_files([('map.txt', synthetic_map_file())])
    values = peak_signal(df, 1050, 1100)
    stats = maps.uniformity(values)
    assert stats['n'] == 12 and 5 < stats['rsd'] < 30
    image = maps.grid(values, maps.coordinates_from_names(df.columns))
    assert image.shape == (3, 4) and image.loc[0, 30] > image.loc[0, 0]  # gain grows with x


def test_grid_coordinates_snake():
    from core.maps import grid_coordinates
    coords = grid_coordinates(list('abcdef'), columns=3, step_x=2, step_y=5, snake=True)
    assert coords.loc['c'].tolist() == [4, 0] and coords.loc['d'].tolist() == [4, 5]  # 2nd row reversed


def test_map_page_with_grid():
    app = new_app('WITec Alpha300 R+', 'maps')
    assert not app.exception
    assert app.metric[0].label == 'RSD'
    app.number_input(key='map_columns').set_value(2).run()
    app.checkbox(key='map_relative').check().run()
    assert not app.exception


#
# # Preprocessing
#
def synthetic_spectrum(spikes=()):
    x = np.arange(400, 1800, 1.0)
    background = 3000 + 4000 * np.exp(-((x - 1100) / 600) ** 2)
    peaks = sum(h * np.exp(-4 * np.log(2) * ((x - c) / w) ** 2)
                for c, h, w in [(520, 3000, 8), (1075, 20000, 12), (1200, 8000, 4), (1588, 15000, 10)])
    y = background + peaks + np.random.default_rng(0).normal(0, 30, x.size)
    clean = y.copy()
    for i, height in spikes:
        y[i] += height
    return x, background, peaks, clean, y


def test_spikes_removed_peaks_kept():
    from core.processing import remove_spikes
    x, _, _, clean, y = synthetic_spectrum(spikes=[(300, 30000), (700, 1500), (900, 20000), (901, 9000)])
    cleaned, removed = remove_spikes(pd.DataFrame({'s': y}, index=x))
    error = np.abs(cleaned['s'].to_numpy() - clean)
    spike_area = [299, 300, 301, 699, 700, 701, 899, 900, 901, 902]
    assert np.delete(error, spike_area).max() == 0  # real peaks (also a narrow 4 cm-1 one) untouched
    assert error[spike_area].max() < 200


@pytest.mark.parametrize('method,param,tolerance', [('modpoly', 5, 0.02), ('arpls', 1e6, 0.01), ('snip', 60, 0.05)])
def test_baseline_methods(method, param, tolerance):
    from core.processing import baselines
    x, background, _, clean, _ = synthetic_spectrum()
    fitted = baselines(pd.DataFrame({'s': clean}, index=x), method, param)['s']
    assert np.max(np.abs(fitted - background)) / 20000 < tolerance


def test_savgol_keeps_peak_height():
    from core.processing import smooth
    x, _, peaks, _, _ = synthetic_spectrum()
    noisy = pd.DataFrame({'s': peaks + np.random.default_rng(1).normal(0, 300, x.size)}, index=x)
    savgol = smooth(noisy, 'savgol', 9)['s'].loc[1580:1596].max()
    average = smooth(noisy, 'moving_average', 9)['s'].loc[1580:1596].max()
    assert abs(savgol - 15000) < abs(average - 15000)


def test_normalizations():
    from core.processing import normalize_by
    x, _, _, clean, _ = synthetic_spectrum()
    df = pd.DataFrame({'a': clean, 'b': 3 * clean}, index=x)
    assert np.allclose(normalize_by(df, 'max').max(), 1)
    assert np.allclose([np.trapezoid(normalize_by(df, 'area')[c], x) for c in 'ab'], 1)
    assert np.allclose(np.sqrt((normalize_by(df, 'vector') ** 2).sum()), 1)
    snv = normalize_by(df, 'snv')
    assert np.allclose(snv.mean(), 0) and np.allclose(snv.std(), 1)
    assert np.allclose(normalize_by(df, 'peak', (1065, 1085)).loc[1065:1085].max(), 1)
    assert np.allclose(normalize_by(df, 'minmax')['a'], normalize_by(df, 'minmax')['b'])


@pytest.mark.parametrize('baseline', ['modpoly', 'arpls', 'snip'])
@pytest.mark.parametrize('normalization', ['none', 'max', 'area', 'vector', 'snv', 'peak'])
def test_visualisation_processing_options(baseline, normalization):
    app = new_app('Renishaw', 'visualisation')
    app.checkbox(key='despike').check().run()
    app.checkbox(key='processed').check().run()
    app.selectbox(key='baseline_method').set_value(baseline).run()
    app.checkbox(key='smoothing').check().run()
    app.selectbox(key='smoothing_method').set_value('savgol').run()
    app.selectbox(key='normalization').set_value(normalization).run()
    app.radio(key='chart_type').set_value('MS').run()
    app.checkbox(key='show_steps').check().run()
    assert not app.exception
    assert app.get('plotly_chart')


#
# # EF presets, uncertainty, AEF
#
PUBLICATION = dict(concentration=1e-6, volume=2.0, wavelength=785, aperture=0.40, size_x=3, size_y=3, development=2,
                   coverage=0.1, depth=2e-3, density=1.3, molecular_weight=154.19, i_sers=40000, i_raman=1000)


def test_ef_uncertainty():
    from core.analysis import ef_from_parameters, ef_uncertainty
    ef = ef_from_parameters(PUBLICATION)
    assert np.isclose(ef, 6.07e7, rtol=0.01)
    result = ef_uncertainty(PUBLICATION, {'coverage': (0.04, 0.18), 'depth': (1e-3, 3e-3)}, {'i_sers': 0.2})
    assert result['low'] < ef < result['high']
    spans = {k: abs(np.log10(b / a)) for k, (a, b) in result['sensitivity'].items()}
    assert max(spans, key=spans.get) == 'coverage'  # literature range 4-18 % dominates


def test_aef():
    from core.analysis import analytical_ef
    assert np.isclose(analytical_ef(40000, 1e-6, 1000, 0.1), 4e6)


def test_ef_presets_and_uncertainty_tile():
    app = new_app(page='ef')
    app.selectbox(key='ef_analyte').set_value('pmba').run()
    app.selectbox(key='ef_objective').set_value('20x').run()
    assert not app.exception
    assert app.number_input(key='ef_na').value == 0.40
    assert app.number_input(key='ef_molecular_weight').value == 154.19
    assert app.number_input(key='ef_cov_low').value == 0.04
    assert next(m for m in app.metric if m.label == 'EF range (90 %)').value != '—'
    app.selectbox(key='ef_analyte').set_value('r6g').run()
    assert app.number_input(key='ef_molecular_weight').value == 479.02 and app.warning
    assert any(m.label == 'AEF' for m in app.metric)


#
# # PCA clustering, loadings
#
def three_groups():
    x = np.arange(400, 1800, 2.0)
    rng = np.random.default_rng(0)

    def spectrum(a, b):
        return 1000 + a * np.exp(-((x - 1075) / 8) ** 2) + b * np.exp(-((x - 1588) / 8) ** 2) + rng.normal(0, 30, x.size)
    columns = {**{f'A{i}': spectrum(5000, 1000) for i in range(6)}, **{f'B{i}': spectrum(1000, 5000) for i in range(6)},
               **{f'C{i}': spectrum(3000, 3000) for i in range(6)}}
    return pd.DataFrame(columns, index=x)


@pytest.mark.parametrize('method', ['kmeans', 'ward'])
def test_clusters_found_automatically(method):
    from core import multivariate
    data = three_groups()
    _, scores, loadings, _ = multivariate.pca(data, 2)
    result = multivariate.cluster(scores, method)
    assert result['k'] == 3 and result['silhouette'] > 0.8
    _, ari = multivariate.agreement([name[0] for name in data.columns], result['labels'])
    assert ari == 1.0
    top_bands = loadings['PC 1'].abs().nlargest(4).index
    assert any(abs(b - 1075) < 5 for b in top_bands) and any(abs(b - 1588) < 5 for b in top_bands)


def test_pca_page_with_clustering():
    app = new_app('Jobin Yvon T64000', 'pca')
    names = app.multiselect(key='pca_group_0').options
    app.multiselect(key='pca_group_0').set_value(names[:1]).run()
    app.multiselect(key='pca_group_1').set_value(names[1:]).run()
    app.checkbox(key='pca_cluster').check().run()
    assert not app.exception
    assert [m.label for m in app.metric][:2] == ['Clusters', 'Silhouette']
    app.checkbox(key='pca_auto_k').uncheck().run()
    app.radio(key='pca_cluster_method').set_value('ward').run()
    assert not app.exception


#
# # Instrument formats: SPC, JCAMP-DX, WDF
#
def raman_like():
    x = np.arange(400.0, 1800.0, 1.0)
    y = 1000 + 20000 * np.exp(-((x - 1075) / 8) ** 2) + 15000 * np.exp(-((x - 1588) / 8) ** 2)
    return x, y


def test_spc_file():
    import spc_io
    x, y = raman_like()
    spc = spc_io.SPC(xarray=x)
    spc.add_subfile(yarray=y)
    spc.add_subfile(yarray=2 * y)
    raw = spc.to_spc_raw().to_bytes()
    loaded = readers.read_file('sample.spc', raw)
    assert loaded.format == 'SPC' and loaded.data.shape == (len(x), 2)
    assert np.isclose(loaded.data.iloc[:, 0].idxmax(), 1075, atol=1)


def test_jcamp_file():
    x, y = raman_like()
    lines = ['##TITLE=sample', '##JCAMP-DX=4.24', '##DATA TYPE=RAMAN SPECTRUM', '##XUNITS=1/CM',
             '##YUNITS=ARBITRARY UNITS', f'##FIRSTX={x[0]}', f'##LASTX={x[-1]}', f'##NPOINTS={len(x)}',
             '##XFACTOR=1', '##YFACTOR=1', '##XYDATA=(X++(Y..Y))']
    lines += [f'{xi:.1f} {yi:.3f}' for xi, yi in zip(x, y)] + ['##END=']
    loaded = readers.read_file('sample.jdx', '\n'.join(lines).encode())
    assert loaded.format == 'JCAMP' and len(loaded.data) == len(x)
    assert np.isclose(loaded.data.iloc[:, 0].idxmax(), 1075, atol=1)


@pytest.mark.skipif(not os.environ.get('SERSITIVIS_WDF_SAMPLES'),
                    reason='set SERSITIVIS_WDF_SAMPLES to a folder with Renishaw *.wdf files')
def test_wdf_files():
    from core import maps
    for path in glob.glob(os.path.join(os.environ['SERSITIVIS_WDF_SAMPLES'], '*.wdf')):
        loaded = read(path)
        assert loaded.format in ('WDF', 'MAP') and not loaded.data.empty
        if loaded.format == 'MAP':
            assert maps.coordinates_from_names(loaded.data.columns) is not None


#
# # PDF reports
#
@pytest.mark.parametrize('page,example,key', [
    ('visualisation', 'Renishaw', 'visualisation'), ('rsd', 'Jobin Yvon T64000', 'rsd'),
    ('calibration', 'Wasatch', 'calibration'), ('maps', 'WITec Alpha300 R+', 'map'), ('ef', None, 'enhancement_factor'),
    ('pca', 'Jobin Yvon T64000', 'pca')])
@pytest.mark.parametrize('language', ['en', 'pl'])
def test_pdf_report(page, example, key, language):
    app = new_app(example, page, language)
    if page == 'pca':
        names = app.multiselect(key='pca_group_0').options
        app.multiselect(key='pca_group_0').set_value(names[:1]).run()
        app.multiselect(key='pca_group_1').set_value(names[1:]).run()
        app.checkbox(key='pca_cluster').check().run()
    if page == 'visualisation':
        app.checkbox(key='peaks').check().run()
    app.button(key=f'{key}_report_create').click().run()
    assert not app.exception
    pdf = app.session_state[f'_{key}_report'][1]
    assert pdf[:5] == b'%PDF-' and len(pdf) > 10000


def test_pca_clustering_with_two_spectra_explains_why():
    app = new_app('Renishaw', 'pca')
    names = app.multiselect(key='pca_group_0').options
    app.multiselect(key='pca_group_0').set_value(names[:1]).run()
    app.multiselect(key='pca_group_1').set_value(names[1:]).run()
    app.checkbox(key='pca_cluster').check().run()
    assert not app.exception
    assert any('3' in w.value for w in app.warning)


def test_single_spectrum_arrows():
    app = new_app(workspace.DEFAULT_EXAMPLE, 'visualisation')
    app.radio(key='chart_type').set_value('SINGLE').run()
    names = list(app.session_state['df'].columns)
    assert app.session_state['single_spectrum'] == names[0]
    app.button(key='single_spectrum_next').click().run()
    assert app.session_state['single_spectrum'] == names[1]
    app.button(key='single_spectrum_prev').click().run()
    app.button(key='single_spectrum_prev').click().run()
    assert app.session_state['single_spectrum'] == names[-1]  # wraps around
    assert not app.exception and app.get('plotly_chart')


@pytest.mark.parametrize('chart', ['GS', 'SINGLE', 'MS'])
def test_reference_peak_highlighted(chart):
    import json
    app = new_app(workspace.DEFAULT_EXAMPLE, 'visualisation')
    app.radio(key='chart_type').set_value(chart).run()
    app.selectbox(key='normalization').set_value('peak').run()
    low, high = app.session_state['reference_peak']
    shapes = json.loads(app.get('plotly_chart')[0].proto.spec)['layout'].get('shapes', [])
    assert not app.exception
    assert any(s.get('type') == 'rect' and (s['x0'], s['x1']) == (low, high) for s in shapes)


@pytest.mark.parametrize('chart', ['GS', 'SINGLE', 'MS', 'P3D'])
def test_background_from_loaded_spectrum(chart):
    app = new_app(workspace.DEFAULT_EXAMPLE, 'visualisation')
    names = list(app.session_state['df'].columns)
    app.radio(key='chart_type').set_value(chart).run()
    app.checkbox(key='bg_subtract').check().run()
    assert app.info  # nothing chosen yet (example names have no 'blank')
    app.multiselect(key='bg_spectra').set_value([names[-1]]).run()
    assert not app.exception and app.get('plotly_chart')
    assert any('scale factor' in c.value for c in app.caption)
    if chart == 'SINGLE':  # background is not offered as a sample
        app.button(key='single_spectrum_next').click().run()
        app.button(key='single_spectrum_next').click().run()
        assert app.session_state['single_spectrum'] == names[0]
    if chart in {'SINGLE', 'MS'}:
        app.checkbox(key='show_steps').check().run()
        assert not app.exception
    app.radio(key='bg_scale').set_value('manual').run()
    app.number_input(key='bg_factor').set_value(0.5).run()
    assert not app.exception and any('0.5' in c.value for c in app.caption)


def test_background_from_separate_file():
    app = new_app(workspace.DEFAULT_EXAMPLE, 'visualisation')
    app.checkbox(key='bg_subtract').check().run()
    app.radio(key='bg_source').set_value('file').run()
    assert app.info
    path = os.path.join(ROOT, 'data', 'data_examples', 'jobin_yvon', '7MPBA_9B22_10s_1x.txt')
    with open(path, 'rb') as f:
        app.session_state['_stored_bg_file'] = [(os.path.basename(path), f.read())]
    app.run()
    assert not app.exception and app.get('plotly_chart')
    assert any('scale factor' in c.value for c in app.caption)
    assert len(app.session_state['df'].columns) == 3


def background_panel(app):
    return next(e for e in app.expander if e.label.startswith('Substrate background'))


def test_background_setting_shared_by_pages():
    app = new_app(workspace.DEFAULT_EXAMPLE, 'visualisation')
    names = list(app.session_state['df'].columns)
    assert background_panel(app).label.endswith(': off')
    app.checkbox(key='bg_subtract').check().run()
    assert background_panel(app).label.endswith(': not set')
    app.multiselect(key='bg_spectra').set_value([names[-1]]).run()
    assert background_panel(app).label.endswith(': on')
    for page in ['rsd', 'calibration', 'maps', 'visualisation']:
        app.switch_page(PAGES[page]).run()
        assert not app.exception
        assert background_panel(app).label.endswith(': on')
        assert app.multiselect(key='bg_spectra').value == [names[-1]]
    app.switch_page(PAGES['rsd']).run()
    assert names[-1] not in app.multiselect(key='rsd_spectra').options
    assert any('scale factor' in c.value for c in app.caption)


@pytest.mark.parametrize('page', ['rsd', 'calibration', 'maps'])
def test_background_on_analysis_pages(page):
    app = new_app('WITec Alpha300 R+', page)
    names = list(app.session_state['df'].columns)
    app.checkbox(key='bg_subtract').check().run()
    app.multiselect(key='bg_spectra').set_value([names[0]]).run()
    assert not app.exception
    assert any('scale factor' in c.value for c in app.caption)
    app.radio(key='bg_scale').set_value('manual').run()
    app.number_input(key='bg_factor').set_value(0.5).run()
    assert not app.exception and any('0.5' in c.value for c in app.caption)


def chart_notes(app):
    import json
    return [a.get('text', '') for chart in app.get('plotly_chart')
            for a in json.loads(chart.proto.spec)['layout'].get('annotations', [])]


@pytest.mark.parametrize('mode', ['snip', 'line', 'none'])
def test_rsd_baseline_switch(mode):
    app = new_app('Jobin Yvon T64000', 'rsd')
    app.radio(key='rsd_baseline').set_value(mode).run()
    assert not app.exception
    columns = list(app.table[0].value.columns)
    assert columns == (['RAW data'] if mode == 'none' else ['RAW data', 'Baseline corrected'])
    assert any(n.startswith('<b>RSD = ') for n in chart_notes(app))


def test_ef_baseline_switch_changes_ef():
    app = AppTest.from_file(os.path.join(ROOT, 'vis.py'), default_timeout=60)
    app.session_state['_ef_source'] = 'spectra'
    app.run()
    app.selectbox(key='workspace_example').set_value('Jobin Yvon T64000').run()
    app.switch_page(PAGES['ef']).run()
    names = app.multiselect(key='ef_Raman_spectra').options
    app.multiselect(key='ef_Raman_spectra').set_value(names[:1]).run()
    app.multiselect(key='ef_SERS_spectra').set_value(names[1:]).run()
    app.slider(key='ef_Raman_range').set_value((1060, 1100)).run()
    app.slider(key='ef_SERS_range').set_value((1060, 1100)).run()
    results = {}
    for mode in ('snip', 'line', 'none'):
        app.radio(key='ef_baseline').set_value(mode).run()
        assert not app.exception
        ef = next(m for m in app.metric if m.label == 'EF').value
        assert any(n.startswith('<b>EF = ') for n in chart_notes(app))  # written on the SERS chart
        results[mode] = ef
    assert len(set(results.values())) > 1


def test_peak_heights_baseline_modes():
    from core.analysis import peak_heights
    x = np.arange(1000, 1150, 1.0)
    peak = 1000 / (1 + ((x - 1075) / 8) ** 2)
    df = pd.DataFrame({'a': peak + 5000 + 20 * (x - 1000), 'b': 2 * peak + 5000 + 20 * (x - 1000)}, index=x)
    line = peak_heights(df, (1030, 1120), mode='line')
    assert np.allclose(line, [1000, 2000], rtol=0.05)  # a straight background is removed
    none = peak_heights(df, (1030, 1120), mode='none')
    assert none['a'] > 6000  # absolute height includes the background
    ratio = peak_heights(df, (1030, 1120), (1030, 1120), mode='line')
    assert np.allclose(ratio, 1)


def saturated_bwtek_file():
    """Example BWTEK file with one raw detector count at the 16-bit limit"""
    path = os.path.join(ROOT, 'data', 'data_examples', 'bwtek', 'bwtek(2).txt')
    lines = open(path, encoding='latin-1').read().splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith('Pixel;'))
    raw_column = lines[header].split(';').index('Raw data #1')
    fields = lines[header + 600].split(';')
    fields[raw_column] = '65535'
    lines[header + 600] = ';'.join(fields)
    return '\n'.join(lines).encode('latin-1')


def test_saturation_detected():
    from core.readers import flat_top
    assert readers.read_file('sat.txt', saturated_bwtek_file()).saturated == ['sat']
    for path in glob.glob(os.path.join(ROOT, 'data', 'data_examples', '*', '*.*')):
        with open(path, 'rb') as f:
            assert not readers.read_file(os.path.basename(path), f.read()).saturated, path
    assert flat_top([1, 5, 9, 9, 9, 4]) and not flat_top([1, 5, 9, 8, 9, 4])


def test_saturation_warning_in_sidebar():
    app = AppTest.from_file(os.path.join(ROOT, 'vis.py'), default_timeout=60)
    app.session_state[workspace.FILES] = [('sat.txt', saturated_bwtek_file())]
    app.run()
    assert not app.exception
    assert any('Detector saturated in: sat' in w.value for w in app.sidebar.warning)


@pytest.mark.parametrize('n,low,high', [(5, 6.0, 29.4), (20, 7.6, 14.7)])
def test_rsd_confidence_interval(n, low, high):
    from core.analysis import rsd_confidence_interval
    interval = rsd_confidence_interval(0.10, n)
    assert np.allclose(np.array(interval) * 100, [low, high], atol=0.1)


def test_morans_i_tells_gradient_from_noise():
    from core import maps
    x, y = np.meshgrid(np.arange(10), np.arange(8))
    coords = pd.DataFrame({'x': x.ravel() * 5.0, 'y': y.ravel() * 2.0}, index=[f'p{i}' for i in range(80)])
    rng = np.random.default_rng(1)
    gradient = maps.morans_i(pd.Series(100 + 3 * x.ravel() + rng.normal(0, 3, 80), index=coords.index), coords)
    assert gradient['i'] > 0.5 and gradient['p'] < 0.01
    random_p = [maps.morans_i(pd.Series(rng.normal(100, 10, 80), index=coords.index), coords, 199)['p']
                for _ in range(10)]
    assert np.median(random_p) > 0.2


@pytest.mark.parametrize('mode', ['snip', 'line', 'none'])
def test_calibration_and_map_baseline_switch(mode):
    app = new_app('Wasatch', 'calibration')
    app.radio(key='cal_baseline').set_value(mode).run()
    assert not app.exception and [m.label for m in app.metric][:3] == ['LOD', 'LOQ', 'R²']
    app = AppTest.from_file(os.path.join(ROOT, 'vis.py'), default_timeout=60)
    app.session_state[workspace.FILES] = [('map.txt', synthetic_map_file())]
    app.run()
    app.switch_page(PAGES['maps']).run()
    app.radio(key='map_baseline').set_value(mode).run()
    assert not app.exception and app.metric[0].label == 'RSD'
    assert any("Moran's I" in m.value for m in list(app.info) + list(app.warning))  # 12 points


def test_visit_counts():
    from vis_helpers.visits import field, file_counts, page_counts
    seen = {}
    assert page_counts(seen, 'start', 'pl') == {'visits': 1, 'pages': {'start': 1}, 'languages': {'pl': 1}}
    assert page_counts(seen, 'start', 'pl') == {}  # a rerun of the same page is not a new view
    assert page_counts(seen, 'rsd', 'en') == {'pages': {'rsd': 1}, 'languages': {'en': 1}}
    loaded = readers.read_files([('a.txt', saturated_bwtek_file())])[1]
    assert file_counts(seen, loaded) == {'formats': {'BWTEK': 1}}
    assert file_counts(seen, loaded) == {}  # the same file counted once
    assert file_counts(seen, [], 'WITec Alpha300 R+') == {'examples': {'WITec_Alpha300_R_': 1}}
    assert field('') == '_'


def test_no_statistics_without_secret():
    """Local runs and tests: no Firestore credentials, nothing is sent and the app works"""
    from vis_helpers import visits
    app = new_app('Renishaw', 'rsd')
    assert not app.exception
    assert app.session_state[visits.SEEN]['visit'] and app.session_state[visits.SEEN]['page'] == 'rsd'


def test_visit_write_to_firestore(monkeypatch):
    """The document of the day gets Firestore increments (fake client - no network, no credentials)"""
    import sys
    import types
    from vis_helpers import visits

    class Increment:
        def __init__(self, n):
            self.n = n

    firestore = types.ModuleType('google.cloud.firestore')
    firestore.Increment = Increment
    cloud = types.ModuleType('google.cloud')
    cloud.firestore = firestore
    monkeypatch.setitem(sys.modules, 'google', types.ModuleType('google'))
    monkeypatch.setitem(sys.modules, 'google.cloud', cloud)
    monkeypatch.setitem(sys.modules, 'google.cloud.firestore', firestore)

    written = []

    class Document:
        def __init__(self, name):
            self.name = name

        def set(self, data, merge):
            written.append((self.name, data, merge))

    client = types.SimpleNamespace(collection=lambda name: types.SimpleNamespace(
        document=lambda day: Document(f'{name}/{day}')))
    monkeypatch.setattr(visits, '_client', lambda: client)

    class Synchronous:  # run the background write at once
        def __init__(self, target, daemon):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(visits.threading, 'Thread', Synchronous)
    visits._send({'visits': 1, 'pages': {'rsd': 1}})
    (name, data, merge), = written
    assert name.startswith('visits/20') and merge
    assert data['visits'].n == 1 and data['pages']['rsd'].n == 1
