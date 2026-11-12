"""
Smoke tests: every example file can be parsed and every app view renders without an exception.
Run from the project root:  python -m pytest tests
"""
import glob
import io
import os

import pytest
from streamlit.testing.v1 import AppTest

from processing import save_read, utils

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = {'BWTEK': 'bwtek', 'RENI': 'renishaw', 'WITEC': 'witec',
           'WASATCH': 'wasatch', 'TELEDYNE': 'teledyne', 'JOBIN': 'jobin_yvon'}
EXAMPLES = [(spec, path) for spec, folder in FOLDERS.items()
            for path in sorted(glob.glob(os.path.join(ROOT, 'data', 'data_examples', folder, '**', '*.*'),
                                         recursive=True))]


@pytest.fixture(autouse=True)
def run_from_root(monkeypatch):
    monkeypatch.chdir(ROOT)


def as_upload(path):
    """Mimics Streamlit's uploaded file (bytes + name)"""
    with open(path, 'rb') as f:
        buffer = io.BytesIO(f.read())
    buffer.name = os.path.basename(path)
    return buffer


@pytest.mark.parametrize('spectrometer,path', EXAMPLES, ids=[os.path.basename(p) for _, p in EXAMPLES])
def test_example_file_parses(spectrometer, path):
    df = save_read.files_to_df([as_upload(path)], spectrometer)
    assert not df.empty
    assert all(dtype.kind in 'fi' for dtype in df.dtypes)
    assert not df.index.duplicated().any()


@pytest.mark.parametrize('spectrometer', FOLDERS)
def test_example_set_parses(spectrometer):
    df = save_read.files_to_df(utils.load_example_files(spectrometer), spectrometer)
    assert df.shape[1] >= 2
    assert df.notna().all().all()


def test_non_utf8_file():
    with open(os.path.join(ROOT, 'data', 'data_examples', 'renishaw', 'renishaw(5).txt'), 'rb') as f:
        content = f.read()
    buffer = io.BytesIO('# próbka żółć\n'.encode('cp1250') + content)
    buffer.name = 'cp1250.txt'
    df = save_read.files_to_df([buffer], 'RENI')
    assert not df.empty


def new_app():
    app = AppTest.from_file('vis.py', default_timeout=60)
    app.run()
    return app


@pytest.mark.parametrize('page', ['Main Page', 'PCA', 'EF', 'RSD'])
def test_page_renders(page):
    app = new_app()
    app.sidebar.selectbox[0].set_value(page).run()
    assert not app.exception


@pytest.mark.parametrize('chart', ['SINGLE', 'MS', 'GS', 'P3D'])
@pytest.mark.parametrize('conversion', ['RAW', 'OPT'])
@pytest.mark.parametrize('spectrometer', FOLDERS)
def test_visualisation(spectrometer, chart, conversion):
    app = new_app()
    app.sidebar.selectbox[0].set_value('visualisation').run()
    app.sidebar.selectbox[1].set_value(spectrometer).run()
    app.sidebar.checkbox[0].check().run()
    app.sidebar.selectbox[2].set_value(chart).run()
    app.sidebar.radio[0].set_value(conversion).run()
    assert not app.exception


def test_ef_matches_publication_example():
    """Values from 'Enhancement Factor (EF): teoria i praktyka', IChF PAN 2020, section 4.3 -> EF = 6.1e7"""
    app = new_app()
    app.sidebar.selectbox[0].set_value('EF').run()
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


def test_baseline_recovers_background_under_peaks():
    """Synthetic spectrum: known polynomial background + Raman-like peaks"""
    import numpy as np

    x = np.linspace(400, 1800, 1500)
    background = 2000 + 1.5 * (x - 400) - 6e-4 * (x - 400) ** 2
    peaks = sum(h * np.exp(-((x - c) / 6) ** 2) for c, h in [(640, 3000), (1080, 20000), (1590, 15000)])
    estimated = utils.baseline(background + peaks, 2, x=x)
    assert np.max(np.abs(estimated - background)) / np.ptp(peaks) < 0.01
