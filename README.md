# SERSitiVIS

Fast and easy processing and visualisation of Raman and SERS spectra – a free web app by
[SERSitive](https://sersitive.eu), maker of SERS substrates.

## What it does

- **Substrate background subtraction** – blank substrate spectrum scaled and subtracted, on every page that
  measures spectra.
- **Visualisation** – grouped, single, mean and 3D spectra; spike removal, baseline correction (ModPoly, arPLS, SNIP), smoothing, six normalisation methods, automatic peak labelling.
- **RSD** – reproducibility of a SERS substrate from many spectra of one sample.
- **Calibration & LOD** – calibration curve from a concentration series, limit of detection (ICH or IUPAC).
- **Uniformity map** – intensity / RSD map of a substrate from mapping data.
- **Enhancement Factor** – analytical (AEF) and substrate EF, with Monte Carlo uncertainty.
- **PCA** – group comparison, clustering, loadings and scree plot.
- Export of charts (PNG, SVG), processed data (CSV) and PDF reports.
- Languages: English, Polish, German, Ukrainian. Light and dark theme.

What changed and when: [CHANGELOG.md](CHANGELOG.md).

## Supported files

The format is detected automatically: BWTEK, Renishaw (incl. WDF), WITec, Wasatch, Jobin Yvon,
Teledyne Princeton Instruments, Galactic SPC, JCAMP-DX and plain text / CSV tables.

## Run locally

Python 3.11:

```
pip install -r requirements.txt
streamlit run vis.py
```

## Tests

```
pip install -r requirements_dev.txt
python -m pytest
```

All library versions are pinned in `requirements.txt` – update them deliberately and run the tests afterwards.

## Project layout

| Folder | Contents |
|---|---|
| `core/` | Pure Python, no Streamlit: file reading, processing, analyses, PDF reports |
| `vis_helpers/` | User interface of each page, translations (`i18n.py`, `lang_de.py`, `lang_uk.py`) |
| `app_pages/` | Page entry points used by `st.navigation` |
| `visualisation/` | Plotly chart helpers |
| `data/` | Example spectra |
| `tests/` | pytest tests (Streamlit AppTest + core functions) |

## Visit statistics

The app counts anonymous numbers per day in Firestore: visits, page views, language, formats of uploaded files,
example data and PDF reports. No cookies, no IP addresses, no file contents. It is on only when the Streamlit
secret `firebase_credentials` (service account JSON) is set - see `vis_helpers/visits.py`.
The SERSitive team sees them at `/statistics` (not in the menu), with the password from the secret
`statistics_password`.

## Contact

developers@sersitive.eu
