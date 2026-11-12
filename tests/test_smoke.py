"""
Smoke tests: example files are read correctly and every app view works on example data.
Run from the project root:  python -m pytest
"""
import glob
import os

import numpy as np
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
def new_app(example=None, page=None):
    app = AppTest.from_file('vis.py', default_timeout=60)
    app.run()
    if example:
        app.selectbox(key='workspace_example').set_value(example).run()
    if page:
        app.selectbox(key='page').set_value(page).run()
    return app


@pytest.mark.parametrize('page', ['Main Page', 'visualisation', 'PCA', 'EF', 'RSD'])
def test_page_renders_without_data(page):
    assert not new_app(page=page).exception


@pytest.mark.parametrize('chart', ['SINGLE', 'MS', 'GS', 'P3D'])
@pytest.mark.parametrize('conversion', ['RAW', 'OPT'])
@pytest.mark.parametrize('instrument', workspace.EXAMPLES)
def test_visualisation(instrument, chart, conversion):
    app = new_app(instrument, 'visualisation')
    app.selectbox(key='chart_type').set_value(chart).run()
    app.radio(key='conversion').set_value(conversion).run()
    assert not app.exception
    assert app.get('plotly_chart')


@pytest.mark.parametrize('instrument', workspace.EXAMPLES)
def test_pca(instrument):
    app = new_app(instrument, 'PCA')
    assert not app.exception
    assert app.get('plotly_chart')


@pytest.mark.parametrize('instrument', workspace.EXAMPLES)
def test_rsd(instrument):
    app = new_app(instrument, 'RSD')
    assert not app.exception
    assert app.table


def test_ef_from_spectra():
    app = new_app('Jobin Yvon T64000', 'EF')
    app.radio[0].set_value('from_spec').run()
    names = app.multiselect(key='ef_Raman_spectra').options
    app.multiselect(key='ef_Raman_spectra').set_value(names[:1]).run()
    app.multiselect(key='ef_SERS_spectra').set_value(names[1:]).run()
    app.slider(key='ef_Raman_range').set_value((1070, 1090)).run()
    app.slider(key='ef_SERS_range').set_value((1070, 1090)).run()
    assert not app.exception
    assert any(m.value.startswith('$EF =$') for m in app.markdown)


def test_ef_matches_publication_example():
    """Values from 'Enhancement Factor (EF): teoria i praktyka', IChF PAN 2020, section 4.3 -> EF = 6.1e7"""
    app = new_app(page='EF')
    inputs = {'Provide "x"': 1, 'Provide "n"': -6, 'Volume of solution [µl]': 2000.0,
              'Laser wavelength [nm]': 785, 'Lens parameter - Numerical Aperture (NA)': 0.40,
              'First dimension (x)': 3.0, 'Second dimension (y)': 3.0,
              'Surface area development coefficient': 2.0,
              'The coverage of the surface by the analyte (0-1)': 0.1,
              'Depth into which the laser penetrates the chemical compound in crystalline form [mm]': 2.0,
              'Compound density [g/cm³]': 1.3, 'Molecular weight [g/mol]': 154.19,
              'Raman Intensity': 1000, 'SERS Intensity': 40000}
    widgets = {w.label: w for w in app.number_input}
    for label, value in inputs.items():
        widgets[label].set_value(value)
    app.run()
    assert not app.exception
    assert any(m.value.startswith('$EF =$') and '6.1e+07' in m.value for m in app.markdown)
