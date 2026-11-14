# Changelog

All notable changes to **SERSitiVIS**, the free Raman & SERS spectra app by [SERSitive](https://sersitive.eu).
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### ✨ New
- **Substrate background subtraction** in Visualisation, RSD, Calibration & LOD and the uniformity map. Removes the
  bands of the bare substrate. The background is either one or more of the loaded spectra (averaged, and no longer
  shown as samples) or a separate file.
  - One *Substrate background* panel, the same on every page. The setting is shared by the pages, and the panel
    header says whether it is on, e.g. *Substrate background: on*.
  - The background is scaled for every spectrum automatically: it is fitted together with a smooth polynomial, and
    analyte peaks are left out of the fit. A fixed factor can be set instead, e.g. 1 when the background was
    measured with the same settings.
  - The scale factor is shown under the setting. The steps view shows the scaled background and the result, and the
    PDF report lists the background used.

- **Detector saturation warning.** When the top of a peak is cut off by the detector, the sidebar says which
  spectrum and why it matters: the peak is too low, so e.g. EF comes out ~10 % lower. BWTEK files are checked against
  the raw detector counts (65 535), other files for a flat, clipped peak top.
- **How certain is the RSD: 95 % confidence interval** in the RSD table and on the RSD, EF and map results. An RSD
  of 10 % measured on 5 spectra can really be anything from 6 % to 29 %; on 20 spectra 8–15 %.
- **Uniformity map: is the non-uniformity random or a gradient?** Moran's I with a permutation test, for maps of at
  least 3 × 3 points. Two maps with the same RSD of 15 % differ: scattered weak points are noise, a weaker edge or
  patch points to the production process.

### 🧪 Processing
- **Baseline under the peak switch above the spectrum** in RSD and EF: *SNIP* (default, the same as
  Visualisation), *Straight line under the peak* or *None (absolute height)*, with the SNIP half window next to it.
  The result is written on the chart and changes at once: *RSD = 12.3 %* on the RSD chart, *EF = 6.1e7* with the
  peak intensity and its RSD on the SERS chart. The subtracted baseline is drawn under the peak as a dotted line.
  Before, RSD always used a line under each peak and EF a 5th degree polynomial. The same switch replaces the
  polynomial degree in Calibration & LOD and in the uniformity map.
- **SNIP half window 40 cm⁻¹ by default** (was 60), on every page. On test spectra with known peak heights, 60 cm⁻¹
  left fluorescence under the narrow p-MBA band at 1075 cm⁻¹ and overestimated it by ~15 %. 40 cm⁻¹ measures it
  within ~5 %. The help text explains the rule: about twice the peak width (FWHM).

### 🎨 Interface
- **SNIP is the default baseline correction method.** It is first in the list, followed by the polynomial (ModPoly)
  and arPLS.
- **Chart type** in Visualisation is now picked from a collapsible panel with options, like *Range*. The panel
  header shows the current choice, e.g. *Chart type: Mean spectrum*.
- A note under the language flags: English is the original version, the other languages are translated by AI.
- **Single spectrum**: browse the spectra with ‹ › arrows instead of a drop-down list. The name and the position
  (e.g. *2 / 3*) are shown between the arrows, and after the last spectrum it starts again from the first.
- Drop-down lists have their own background, border and shadow, so they no longer blend into the panel behind them
  (light and dark theme).

### 🐛 Fixes
- **Reference peak normalisation**: the reference peak range is now highlighted on the chart and can be selected
  by dragging on it, like the peak ranges on the other pages.
- **Dark theme**: highlighted peak ranges (RSD, calibration, map, EF, reference peak) use a lighter gold with an
  outline. Before, they turned a hard-to-see olive.
- **Supported files** (manual): the example file previews are readable in the dark theme and no longer use
  `st.components.v1.html`, which Streamlit is removing (it filled the server log with warnings).

### 📚 Project
- `README.md` describes the app, supported files, running it locally and running the tests.
- Removed the outdated `requirements_conda.txt` (a 2020 Anaconda environment: Python 3.7, Streamlit 0.80).

---

## [2.0.0] – 2026-11-13

The biggest update since the app was launched: a rebuilt core, five new analyses, more file formats,
four languages and PDF reports.

### ✨ New analyses

**📈 Calibration & LOD** – a new page
- Calibration curve from a concentration series: peak height or area after a local baseline.
- Concentrations read from file names (`5x10-4M`, `10-3M`, `1ppm`, `0.5 mM`…) and editable in a table.
  Changing the unit converts the values.
- Replicates averaged (mean ± SD, RSD). Linear or log₁₀ concentration axis, R², equation.
- **LOD / LOQ** from the residual SD (ICH: 3.3·s/slope, 10·s/slope) or from blank spectra (IUPAC: 3·s/slope).
  Not reported when the signal does not increase with concentration.
- The strongest peak is selected automatically, so results appear straight away.

**🗺️ Uniformity map** – a new page
- Map files (X, Y, Raman Shift, Intensity, e.g. Renishaw WiRE) are recognised automatically.
- Ordinary spectra can be placed on a grid (points per row, step, snake order).
- Heatmap (absolute or % of mean), RSD, mean, min/max, share of points within ±20 % of the mean, histogram.

**📍 Peak detection** in Visualisation
- Peaks found and labelled with their position. Adjustable sensitivity, minimal distance and number of labels.
- Peak table with position, intensity, prominence and FWHM, exported to CSV.

**⚡ Enhancement Factor**
- **Analytical EF (AEF)** tab: AEF = (I<sub>SERS</sub> / c<sub>SERS</sub>) / (I<sub>Raman</sub> / c<sub>Raman</sub>).
- **Presets**: full p-MBA parameter set. 4-ATP, R6G and crystal violet set the molar mass only.
  Typical objective NAs are included.
- **Uncertainty**: 20 000 Monte Carlo draws give a 90 % range next to the EF. A sensitivity chart shows which input
  matters most (usually surface coverage).
- Parameters can be saved and loaded back from the file of a previous calculation.
- Compact form with result tiles. The calculation is shown step by step.

**🔬 PCA**
- Clustering of PCA scores with k-means or hierarchical clustering (Ward). The number of clusters is chosen by
  silhouette or set by hand.
- Agreement with the groups (adjusted Rand index) and a cross-table.
- Loadings chart with the bands that drive PC 1, and a scree plot.
- Files uploaded separately for each group, plus optional spectra from the sidebar.

### 🧪 Better processing
- **Spike (cosmic ray) removal** that leaves real peaks untouched.
- **Baseline**: polynomial (ModPoly), arPLS and SNIP. The polynomial method is now more accurate: the old one could
  leave the baseline up to ~15 % too high.
- **Smoothing**: moving average or Savitzky–Golay.
- **Normalisation**: min-max, maximum, area, vector, SNV and reference peak (internal standard).
- *Show baseline and intermediate steps* view for single and mean spectra.

### 📂 Files
- **The file format is detected automatically.** You no longer need to pick a spectrometer, and files from different
  instruments can be uploaded together.
- New formats: **Renishaw WDF** (spectra, series, line scans and maps), **Galactic SPC** and **JCAMP-DX**.
- Better reading of text files: decimal commas, Central-European encodings, headers, multiple Raman Shift columns
  (WITec) and duplicate names. A file that cannot be read is reported and the app keeps working.
- **Full spectral resolution kept.** Spectra are aligned by interpolation instead of rounding the Raman shift to whole
  numbers, which used to drop points (e.g. 901 of 3390 for Jobin Yvon).

### 📄 Reports & export
- **PDF report** on every results page: settings, files, results, charts, tables and the method used.
- High-resolution PNG and SVG charts, CSV everywhere.

### 🧭 Navigation & look
- New menu with icons and a **start page**: quick guide, *Try with example data* button and a link to sersitive.eu.
- Spectra are uploaded **once** in the sidebar and shared by all pages. They are kept when you switch pages.
  A *Clear data* button empties them.
- **Four languages**: English, Polish, German and Ukrainian, switched with flags at the bottom of the sidebar.
- **Light and dark theme**, following the system setting. Charts adapt to the theme.
- The SERSitive colour palette is used by default. Other chart options are under *Chart appearance*.
- For RSD, EF and calibration, the peak range can be **selected by dragging on the chart**.
- Larger, sharper SERSitive logo in the sidebar.

### 🐛 Fixes
- **RSD**: *Normalise* made the RSD of the strongest peak always 0 %. Normalisation now changes only the chart.
- **RSD**: the default baseline under a peak is a straight line, because higher degrees cut into the peak.
  The fitted baselines are drawn on the chart.
- **EF**: corrected units and step descriptions. All uploaded spectra are averaged, and Raman and SERS have
  separate peak ranges.
- Single spectrum, Mean spectrum and the optimised view no longer crash.
- Wasatch file names are cleaned correctly.

### 🛠️ Under the hood
- Calculations moved to a Streamlit-independent `core/` package. The interface lives in `vis_helpers/` and
  `app_pages/`.
- Replaced the abandoned PeakUtils with pybaselines.
- Streamlit 1.67 with all libraries pinned to tested versions. Unused packages removed.
- Over 230 automated tests: every page with every example data set, file formats and all translations.

---

## [1.x] – 2020 – 2025

The original SERSitiVIS.

- **2025** – library version conflicts resolved, Dev Container added.
- **2022** – updated to newer Streamlit, adjustable polynomial degree in RSD, RSD table formatting.
- **2021** – PCA with spectrum groups and baseline correction, RSD (formerly RMSE), Enhancement Factor
  calculator, custom colour palettes, home page with logo, baseline subtraction and smoothing, error monitoring.
- **2020** – first version: spectra visualisation with chart templates and colours, single and mean spectrum,
  baseline view.

[Unreleased]: https://github.com/czubert/SERSitiVIS/compare/v2.0.0...master
[2.0.0]: https://github.com/czubert/SERSitiVIS/releases/tag/v2.0.0
[1.x]: https://github.com/czubert/SERSitiVIS/commit/d60ce6b
