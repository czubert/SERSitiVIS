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
         'calibration': 'app_pages/calibration.py'}


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


@pytest.mark.parametrize('language', ['en', 'pl'])
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
    app.selectbox(key='chart_type').set_value(chart).run()
    if processed:
        app.checkbox(key='processed').check().run()
        app.checkbox(key='normalized').check().run()
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
    assert app.metric[0].label == 'EF'


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
    assert app.metric[0].value == '6.1e+07'


def test_rsd_not_affected_by_chart_normalisation():
    """Normalising each spectrum to its maximum made RSD of the strongest peak 0 %"""
    app = new_app('Jobin Yvon T64000', 'rsd')
    before = app.table[0].value.astype(float)
    assert before.loc['RSD[%]', 'RAW data'] > 1
    app.checkbox(key='rsd_normalize').check().run()
    assert app.table[0].value.astype(float).equals(before)


def test_rsd_polynomial_degree_changes_result():
    app = new_app('Jobin Yvon T64000', 'rsd')
    app.slider(key='rsd_Peak 1_range').set_value((1050, 1110)).run()
    results = []
    for degree in (1, 10):
        app.slider(key='rsd_degree').set_value(degree).run()
        results.append(app.table[0].value.astype(float).loc['RSD[%]', 'Baseline corrected'])
    assert results[0] != results[1]


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


def test_every_text_has_polish_translation():
    from vis_helpers.i18n import PL
    missing = sorted(text for text in translated_texts() if text not in PL)
    assert not missing, missing


@pytest.mark.parametrize('page', PAGES)
def test_language_switch_keeps_choices(page):
    app = new_app('Renishaw', 'visualisation')
    app.selectbox(key='chart_type').set_value('MS').run()
    app.switch_page(PAGES[page]).run()
    app.radio(key='_lang_widget').set_value('pl').run()
    assert not app.exception
    app.switch_page(PAGES['visualisation']).run()
    assert not app.exception
    assert app.selectbox(key='chart_type__pl').value == 'MS'
    assert app.session_state['_ws_example'] == 'Renishaw'
    app.radio(key='_lang_widget').set_value('en').run()
    assert not app.exception and app.selectbox(key='chart_type').value == 'MS'


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
