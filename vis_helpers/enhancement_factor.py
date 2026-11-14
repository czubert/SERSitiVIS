"""
Enhancement Factor calculator.
Method: 'Enhancement Factor (EF): teoria i praktyka', P. Piecyk, A. Kowalska, T. Szymborski, IChF PAN 2020.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import analysis
from vis_helpers import data_customisation, vis_utils
from vis_helpers.i18n import t, choice

SPECTRA_TYPES = ['Raman', 'SERS']

# Tabs styled like folder / binder tabs in SERSitive colours: gold (AEF), blue (substrate EF)
_TAB_COLORS = {'light': ([('#E9D3A8', '#FBF6EC'), ('#B9D0E4', '#EEF4FA')], '#b5c0cc', '#1F2329'),  # (tab, panel),
               'dark': ([('#7A6639', '#211D16'), ('#2F5170', '#17202B')], '#3A4452', '#F1F4F8')}  # border, text
_TABS = '.st-key-ef_tabs [data-testid="stTabs"]'


def folder_tabs_css():
    colors, border, text = _TAB_COLORS['dark' if vis_utils.is_dark() else 'light']
    return '<style>' + ' '.join([
        f'{_TABS} [role="tablist"] {{gap: 6px; border-bottom: none; padding-left: 4px;}}',
        f'{_TABS} [data-testid="stTab"] {{padding: 10px 22px; border-radius: 12px 12px 0 0; border: 1px solid {border}; '
        f'border-bottom: none; font-weight: 600; opacity: 0.6; margin-bottom: -1px;}}',
        f'{_TABS} [data-testid="stTab"][data-selected="true"] {{opacity: 1; position: relative; z-index: 1;}}',
        f'{_TABS} [data-testid="stTab"] p {{font-size: 1.05rem; color: {text};}}',
        f'{_TABS} .react-aria-SelectionIndicator {{display: none;}}',
        f'{_TABS} [data-testid="stTabPanel"] {{border: 1px solid {border}; border-radius: 0 12px 12px 12px; '
        f'padding: 1.25rem;}}',
        *[f'{_TABS} [data-testid="stTab"]:nth-child({i}) {{background: {tab};}} '
          f'{_TABS}:has([data-testid="stTab"]:nth-child({i})[data-selected="true"]) [data-testid="stTabPanel"] '
          f'{{background: {panel}; border-top: 4px solid {tab};}}'
          for i, (tab, panel) in enumerate(colors, start=1)],
    ]) + '</style>'


# Inputs that can be saved to / loaded from a file: widget key -> (type, min, max, unit)
PARAMETERS = {
    'ef_conc_x': (int, 1, 9, 'x (C = x·10ⁿ mol/dm³)'),
    'ef_conc_n': (int, -15, 0, 'n (C = x·10ⁿ mol/dm³)'),
    'ef_volume': (float, 0.0, 10000.0, 'µl'),
    'ef_wavelength': (int, 450, 1200, 'nm'),
    'ef_na': (float, 0.01, 10.0, 'NA'),
    'ef_size_x': (float, 0.1, 50.0, 'mm'),
    'ef_size_y': (float, 0.1, 50.0, 'mm'),
    'ef_development': (float, 0.1, 10.0, ''),
    'ef_coverage': (float, 0.0, 1.0, ''),
    'ef_density': (float, 0.001, 20.0, 'g/cm³'),
    'ef_molecular_weight': (float, 0.001, 1000.0, 'g/mol'),
    'ef_depth': (float, 0.0, 10.0, 'mm'),
    'ef_i_raman': (int, 1, 1000000, 'a.u.'),
    'ef_i_sers': (int, 1, 10000000, 'a.u.'),
}
# Analyte presets. p-MBA: values from 'Enhancement Factor (EF): teoria i praktyka' (IChF PAN 2020), coverage range
# 4-18 % from the literature cited there. Other analytes: only the molar mass is certain - density, coverage and
# penetration depth must be taken from the literature (the publication says so explicitly).
ANALYTES = {
    'custom': {},
    'pmba': {'ef_molecular_weight': 154.19, 'ef_density': 1.3, 'ef_coverage': 0.1, 'ef_depth': 2.0},
    '4atp': {'ef_molecular_weight': 125.19},
    'r6g': {'ef_molecular_weight': 479.02},
    'cv': {'ef_molecular_weight': 407.98},
}
ANALYTE_LABELS = {'custom': 'Custom', 'pmba': 'p-MBA (4-mercaptobenzoic acid)', '4atp': '4-ATP (4-aminothiophenol)',
                  'r6g': 'Rhodamine 6G', 'cv': 'Crystal violet'}
COVERAGE_RANGE = {'pmba': (0.04, 0.18)}
# typical numerical apertures - check the value engraved on your objective
OBJECTIVES = {'custom': None, '10x': 0.25, '20x': 0.40, '50x LWD': 0.50, '50x': 0.75, '100x': 0.90}


def short(value):
    """7.2e+07 -> 7.2e7"""
    return f'{value:.1e}'.replace('e+0', 'e').replace('e-0', 'e-').replace('e+', 'e')


def apply_analyte():
    analyte = st.session_state['_ef_analyte']
    for key, value in ANALYTES[analyte].items():
        st.session_state[key] = value
    if analyte in COVERAGE_RANGE:
        st.session_state['ef_cov_low'], st.session_state['ef_cov_high'] = COVERAGE_RANGE[analyte]


def apply_objective():
    aperture = OBJECTIVES[st.session_state['_ef_objective']]
    if aperture:
        st.session_state['ef_na'] = aperture


# files exported by the previous version: label -> (key, conversion)
OLD_FORMAT = {'V [ml]': ('ef_volume', 1000), 'λ [nm]': ('ef_wavelength', 1), 'NA': ('ef_na', 1),
              'coverage': ('ef_coverage', 1), 'd [g/cm³]': ('ef_density', 1), 'M [g/mol]': ('ef_molecular_weight', 1),
              'h [m]': ('ef_depth', 1000), 'I Raman': ('ef_i_raman', 1), 'I SERS': ('ef_i_sers', 1)}


def parse_parameters(raw):
    """
    Reads EF parameters from a CSV file downloaded from this page (current or previous format)
    :param raw: bytes
    :return: (dict {widget key: value}, list of keys that were out of range and skipped)
    """
    import io
    table = pd.read_csv(io.BytesIO(raw), encoding='utf-8')
    values = {}
    if 'key' in table.columns:
        values = {k: v for k, v in zip(table['key'], table['value']) if k in PARAMETERS}
    else:  # previous format: two columns - label, value
        for label, value in zip(table.iloc[:, 0], table.iloc[:, 1]):
            if label in OLD_FORMAT:
                key, factor = OLD_FORMAT[label]
                values[key] = float(value) * factor
            elif label == 'C [mol/dm³]' and float(value) > 0:
                exponent = int(np.floor(np.log10(float(value))))
                values['ef_conc_x'] = round(float(value) / 10 ** exponent)
                values['ef_conc_n'] = exponent

    loaded, skipped = {}, []
    for key, value in values.items():
        kind, low, high, _ = PARAMETERS[key]
        try:
            value = kind(round(float(value)) if kind is int else float(value))
        except (TypeError, ValueError):
            skipped.append(key)
            continue
        if low <= value <= high:
            loaded[key] = value
        else:
            skipped.append(key)
    return loaded, skipped


def load_parameters():
    """file_uploader callback - fills the inputs with values from the file"""
    uploaded = st.session_state.get('ef_parameters_file')
    if not uploaded:
        return
    try:
        loaded, skipped = parse_parameters(uploaded.getvalue())
    except Exception:
        st.session_state['_ef_load_message'] = ('error', t('This is not a parameters file downloaded from this page.'))
        return
    for key, value in loaded.items():
        st.session_state[key] = value
    if 'ef_i_raman' in loaded or 'ef_i_sers' in loaded:
        st.session_state['_ef_source'] = 'input'
        st.session_state.pop('ef_source', None)
    message = t('Loaded {n} parameters.').format(n=len(loaded))
    if skipped:
        message += ' ' + t('Skipped (out of range): {keys}').format(keys=', '.join(skipped))
    st.session_state['_ef_load_message'] = ('success' if loaded else 'error', message)


def main(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    st.header(t('Enhancement Factor (EF) calculator'))
    st.html(folder_tabs_css())
    with st.container(key='ef_tabs'):
        aef_tab, substrate_tab = st.tabs([t('Analytical EF (AEF)'), t('Substrate EF')])
    with aef_tab:
        analytical()
    with substrate_tab:
        substrate_ef(df)


def analytical():
    """AEF = (I_SERS / c_SERS) / (I_Raman / c_Raman)"""
    st.caption(t('Simpler definition, often used to compare substrates: signal per concentration in SERS divided by '
                 'signal per concentration in normal Raman (analyte solution measured under the same conditions).'))
    cols = st.columns(2)
    values = {}
    for col, name, default_exponent, default_intensity in [(cols[0], 'SERS', -6, 60000), (cols[1], 'Raman', -1, 1000)]:
        with col.container(border=True):
            st.markdown(f'##### {name}')
            c = st.columns(2)
            x = c[0].number_input(t('Concentration') + ' x', 1, 9, 1, key=f'aef_{name}_x')
            n = c[1].number_input('× 10ⁿ mol/dm³, n', -15, 1, default_exponent, key=f'aef_{name}_n')
            label = t('SERS Intensity') if name == 'SERS' else t('Raman Intensity')
            intensity = st.number_input(label, 1, 10000000, default_intensity, key=f'aef_{name}_i')
            values[name] = (intensity, x * 10.0 ** n)
    aef = analysis.analytical_ef(values['SERS'][0], values['SERS'][1], values['Raman'][0], values['Raman'][1])
    st.metric('AEF', f'{aef:.1e}', border=True)
    st.latex(r'AEF = \frac{I_{SERS} / c_{SERS}}{I_{Raman} / c_{Raman}}')


def substrate_ef(df):
    """Substrate EF (method of the IChF PAN publication) with presets and uncertainty"""
    cols = st.columns(2)
    with cols[0]:
        analyte = choice('selectbox', t('Analyte preset'), list(ANALYTES), key='ef_analyte',
                         format_func=lambda a: t(ANALYTE_LABELS[a]), on_change=apply_analyte)
    with cols[1]:
        choice('selectbox', t('Objective preset (NA)'), list(OBJECTIVES), key='ef_objective',
               format_func=lambda o: t('Custom') if o == 'custom' else f'{o} - NA {OBJECTIVES[o]:.2f}',
               on_change=apply_objective,
               help=t('Typical values - check the numerical aperture engraved on your objective.'))
    if analyte not in ('custom', 'pmba'):
        st.warning(t('Only the molar mass is set for this analyte. Take density, surface coverage and penetration '
                     'depth from the literature - they differ between molecules.'))

    with st.expander(t('Load parameters from a previous calculation file'), icon=':material/history:'):
        st.caption(t('At the bottom of this page you can download all parameters and results with '
                     '"Download parameters and results (CSV)". Upload that file here to restore the calculation '
                     '- e.g. the settings of your microscope - instead of typing them again.'))
        st.file_uploader(t('CSV file downloaded earlier from this page'), type=['csv'],
                         key='ef_parameters_file', on_change=load_parameters)
    if '_ef_load_message' in st.session_state:
        kind, message = st.session_state.pop('_ef_load_message')
        (st.success if kind == 'success' else st.error)(message)
    result = st.container()

    # # Inputs
    cols = st.columns(3)
    with cols[0].container(border=True):
        st.markdown(f'##### :material/science: {t("Solution")}')
        c = st.columns(2)
        multiplier = c[0].number_input(t('Concentration') + ' x', 1, 9, 1, key='ef_conc_x')
        exponent = c[1].number_input('× 10ⁿ mol/dm³, n', -15, 0, -6, key='ef_conc_n')
        concentration = multiplier * 10 ** exponent
        volume = st.number_input(t('Volume of solution [µl]'), 0.0, 10000.0, 2000.0, 10.0, key='ef_volume') / 1000

    with cols[1].container(border=True):
        st.markdown(f'##### :material/biotech: {t("Instrument")}')
        wavelength = st.number_input(t('Laser wavelength [nm]'), 450, 1200, 785, key='ef_wavelength')
        aperture = st.number_input(t('Lens parameter - Numerical Aperture (NA)'), 0.01, 10.0, 0.22, 0.01,
                                   key='ef_na')

    with cols[2].container(border=True):
        st.markdown(f'##### :material/grid_on: {t("SERS substrate")}')
        c = st.columns(2)
        size_x = c[0].number_input(t('Size x [mm]'), 0.1, 50.0, 5.0, 0.1, key='ef_size_x')
        size_y = c[1].number_input(t('Size y [mm]'), 0.1, 50.0, 4.0, 0.1, key='ef_size_y')
        development = st.number_input(t('Surface area development coefficient'), 0.1, 10.0, 2.0, 0.05,
                                      key='ef_development', help=t('Rough surface ~2'))
        coverage = st.number_input(t('The coverage of the surface by the analyte (0-1)'), 0.0, 1.0, 0.1, 0.05,
                                   key='ef_coverage', help=t('e.g. ~0.1 for p-MBA 10⁻⁶ M'))

    cols = st.columns((1, 2))
    with cols[0].container(border=True):
        st.markdown(f'##### :material/hexagon: {t("Compound (solid, for Raman reference)")}')
        density = st.number_input(t('Compound density [g/cm³]'), 0.001, 20.0, 1.3, 0.1, key='ef_density')
        molecular_weight = st.number_input(t('Molecular weight [g/mol]'), 0.001, 1000.0, 154.19, 0.01,
                                           key='ef_molecular_weight')
        depth = st.number_input(t('Depth into which the laser penetrates the chemical compound in crystalline form '
                                  '[mm]'), 0.0, 10.0, 2.0, 0.1, key='ef_depth') / 1000

    # # Calculation (all but the intensities, so the SERS chart can show EF while the peak is chosen)
    n = analysis.num_of_molecules(concentration, volume)
    s_laser = analysis.laser_spot_diameter(wavelength, aperture)
    s0 = analysis.laser_spot_area(s_laser)
    s_platform = size_x * size_y * 10 ** (-6) * development
    n_sers = analysis.n_sers(n, s0, coverage, s_platform)
    v_compound = s0 * depth
    n_raman = analysis.n_raman(s0, depth, density, molecular_weight)

    with cols[1].container(border=True):
        st.markdown(f'##### :material/show_chart: {t("Intensities")}')
        source = choice('radio', t('Intensities'), ['input', 'spectra'], key='ef_source', horizontal=True,
                        label_visibility='collapsed',
                        format_func=lambda s: t('Type in the intensities') if s == 'input'
                        else t('Read them from uploaded spectra'))
        measured_rsd, peak_baseline = {}, None
        if source == 'spectra':
            intensities = intensities_from_spectra(
                df, lambda i_raman, i_sers: analysis.enhancement_factor(i_sers, n_sers, i_raman, n_raman))
            if intensities is None:
                return
            i_raman, i_sers, measured_rsd, peak_baseline = intensities
        else:
            c = st.columns(2)
            i_raman = c[0].number_input(t('Raman Intensity'), 1, 1000000, 1000, 100, key='ef_i_raman')
            i_sers = c[1].number_input(t('SERS Intensity'), 1, 10000000, 60000, 1000, key='ef_i_sers')

    ef = analysis.enhancement_factor(i_sers, n_sers, i_raman, n_raman)

    # # Uncertainty (Monte Carlo)
    with st.expander(t('Uncertainty of EF'), icon=':material/error_med:'):
        st.caption(t('EF depends on assumptions that are hard to measure. The range comes from 20 000 random '
                     'combinations of the uncertain inputs (uniform within the ranges, normal for intensities).'))
        c = st.columns(3)
        default_coverage = COVERAGE_RANGE.get(analyte, (round(coverage * 0.5, 3), round(min(1.0, coverage * 1.5), 3)))
        cov_low = c[0].number_input(t('Coverage from'), 0.0, 1.0, default_coverage[0], 0.01, key='ef_cov_low')
        cov_high = c[0].number_input(t('Coverage to'), 0.0, 1.0, default_coverage[1], 0.01, key='ef_cov_high')
        dev_spread = c[1].slider(t('Surface development ± [%]'), 0, 90, 30, key='ef_dev_spread')
        depth_spread = c[1].slider(t('Penetration depth ± [%]'), 0, 90, 50, key='ef_depth_spread')
        sers_rsd = c[2].slider(t('SERS intensity RSD [%]'), 0, 100,
                               int(round(100 * measured_rsd.get('SERS', 0.2))), key='ef_sers_rsd',
                               help=t('From the uploaded spectra when several SERS spectra are averaged.'))
        raman_rsd = c[2].slider(t('Raman intensity RSD [%]'), 0, 100,
                                int(round(100 * measured_rsd.get('Raman', 0.1))), key='ef_raman_rsd')

    nominal = dict(concentration=concentration, volume=volume, wavelength=wavelength, aperture=aperture,
                   size_x=size_x, size_y=size_y, development=development, coverage=coverage, depth=depth,
                   density=density, molecular_weight=molecular_weight, i_sers=i_sers, i_raman=i_raman)
    ranges = {'coverage': (min(cov_low, cov_high), max(cov_low, cov_high)),
              'development': (development * (1 - dev_spread / 100), development * (1 + dev_spread / 100)),
              'depth': (depth * (1 - depth_spread / 100), depth * (1 + depth_spread / 100))}
    ranges = {key: value for key, value in ranges.items() if 0 < value[0] < value[1]}
    relative_sd = {key: value / 100 for key, value in (('i_sers', sers_rsd), ('i_raman', raman_rsd)) if value}
    uncertainty = analysis.ef_uncertainty(nominal, ranges, relative_sd) if ranges or relative_sd else None

    with result:
        c = st.columns((1, 1.5, 1, 1, 1))
        c[0].metric('EF', f'{ef:.1e}', border=True)
        c[1].metric(t('EF range (90 %)'), f'{short(uncertainty["low"])} – {short(uncertainty["high"])}'
                    if uncertainty else '—', border=True)
        c[2].metric('N SERS', f'{n_sers:.1e}', border=True)
        c[3].metric('N Raman', f'{n_raman:.1e}', border=True)
        c[4].metric('I SERS / I Raman', f'{i_sers / i_raman:.1f}', border=True)

    if uncertainty:
        names = {'coverage': t('Surface coverage'), 'development': t('Surface development'),
                 'depth': t('Penetration depth'), 'i_sers': t('SERS Intensity'), 'i_raman': t('Raman Intensity')}
        sensitivity = uncertainty['sensitivity']
        order = sorted(sensitivity, key=lambda k: abs(np.log10(sensitivity[k][1] / sensitivity[k][0])))
        tornado = go.Figure()
        for key in order:
            tornado.add_trace(go.Scatter(x=list(sensitivity[key]), y=[names[key]] * 2, mode='lines+markers',
                                         line=dict(width=14, color=vis_utils.sersitive_palette()[1]),
                                         marker=dict(size=4, color=vis_utils.sersitive_palette()[0]),
                                         showlegend=False, hovertemplate='%{x:.2e}<extra></extra>'))
        tornado.add_vline(x=ef, line_dash='dash', line_color=vis_utils.sersitive_palette()[2])
        tornado.update_xaxes(type='log', title='EF')
        tornado.update_layout(height=80 + 45 * len(order), margin=dict(t=20, l=10, r=10, b=40),
                              paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        with st.expander(t('Which input changes EF the most'), icon=':material/bar_chart:'):
            st.plotly_chart(tornado, width='stretch', config={'displaylogo': False})
            st.caption(t('Each bar: EF when only this input goes from the low to the high end of its range.'))

    steps = [
        (t('Number of molecules in the solution'), r'N = N_A \cdot C \cdot V', n, ''),
        (t('Laser spot diameter'), r'S_{Laser} = \frac{1.22 \cdot \lambda}{NA}', s_laser, 'm'),
        (t('Laser spot area'), r'S_0 = \pi \cdot \left(\frac{S_{Laser}}{2}\right)^2', s0, 'm²'),
        (t('Molecules on the irradiated SERS surface'),
         r'N_{SERS} = \frac{N \cdot S_0 \cdot coverage}{S_{Platform}}', n_sers, ''),
        (t('Irradiated volume of the solid compound'), r'V_{compound} = S_0 \cdot h', v_compound, 'm³'),
        (t('Molecules irradiated in the Raman measurement'),
         r'N_{Raman} = \frac{d \cdot V_{compound}}{M} \cdot N_A', n_raman, ''),
        ('EF', r'EF = \frac{I_{SERS}}{N_{SERS}} \cdot \frac{N_{Raman}}{I_{Raman}}', ef, ''),
    ]
    with st.expander(t('Show calculation step by step'), icon=':material/function:'):
        for i, (name, formula, value, unit) in enumerate(steps, start=1):
            c = st.columns((2, 3, 1.2), vertical_alignment='center')
            c[0].markdown(f'**{i}. {name}**')
            c[1].latex(formula)
            c[2].markdown(f'{value:.2e} {unit}')
        st.caption(t('Method: P. Piecyk, A. Kowalska, T. Szymborski, IChF PAN 2020.'))

    # 'key' column lets the file be loaded back (Load parameters from a file)
    inputs = {'ef_conc_x': multiplier, 'ef_conc_n': exponent, 'ef_volume': volume * 1000,
              'ef_wavelength': wavelength, 'ef_na': aperture, 'ef_size_x': size_x, 'ef_size_y': size_y,
              'ef_development': development, 'ef_coverage': coverage, 'ef_density': density,
              'ef_molecular_weight': molecular_weight, 'ef_depth': depth * 1000,
              'ef_i_raman': i_raman, 'ef_i_sers': i_sers}
    rows = [(key, key.removeprefix('ef_'), value, PARAMETERS[key][3]) for key, value in inputs.items()]
    rows += [(f'result_{i}', name, value, unit) for i, (name, _, value, unit) in enumerate(steps, start=1)]
    parameters = pd.DataFrame(rows, columns=['key', 'parameter', 'value', 'unit'])
    vis_utils.download_csv(parameters, 'enhancement_factor.csv', t('Download parameters and results (CSV)'),
                           'ef_csv', index=False)
    vis_utils.report_button('enhancement_factor',
                            lambda: build_report(inputs, steps, ef, uncertainty, analyte, peak_baseline),
                            (tuple(inputs.values()), analyte, None if not uncertainty else uncertainty['low'],
                             peak_baseline))


def intensities_from_spectra(df, ef_of):
    """
    Peak intensities read from the uploaded spectra
    :param ef_of: function (I Raman, I SERS) -> EF, the result is written on the SERS chart
    :return: (I Raman, I SERS, {name: measured RSD of the peak intensity}, baseline description) or None
    """
    if df is None:
        st.warning(t('Upload Raman and SERS spectra in the sidebar'))
        return None

    st.caption(t('Choose which uploaded spectra are Raman and which are SERS. Several spectra of each type '
                 '(e.g. from a map) are averaged. Choose the same band in both, e.g. ~1075 or ~1588 cm⁻¹ for p-MBA.'))
    spectra = {}
    for col, name in zip(st.columns(2), SPECTRA_TYPES):
        with col:
            label = t('Raman spectra') if name == 'Raman' else t('SERS spectra')
            chosen = st.multiselect(label, list(df.columns), key=f'ef_{name}_spectra')
            if chosen:
                spectra[name] = df[chosen]
            else:
                st.warning(t('Choose {name} spectra').format(name=name))
    if len(spectra) < 2:
        return None

    mode, half_window = data_customisation.peak_baseline_switch('ef')
    baseline_text = data_customisation.describe_peak_baseline(mode, half_window)
    st.caption(t('Tip: drag on the chart to select the peak range.'))
    cols = st.columns(2)
    limits, ranges, peaks, baselines = {}, {}, {}, {}
    for col, name in zip(cols, SPECTRA_TYPES):
        limits[name] = vis_utils.spectrum_limits(spectra[name])
        with col:
            # separate range for each spectrum - the same band is usually shifted by a few cm-1
            label = t('Raman peak range') if name == 'Raman' else t('SERS peak range')
            ranges[name] = vis_utils.range_slider(label, *limits[name], key=f'ef_{name}_range')
        window, baselines[name] = analysis.peak_window(spectra[name], *ranges[name], mode, half_window)
        peaks[name] = analysis.peak_intensity(window - baselines[name], *ranges[name])
    ef = ef_of(peaks['Raman']['intensity'], peaks['SERS']['intensity']) if all(peaks.values()) else None

    for col, name in zip(cols, SPECTRA_TYPES):
        spectra_df, peak, (low, high) = spectra[name], peaks[name], limits[name]
        range_key, chart_key = f'ef_{name}_range', f'ef_{name}_chart'
        plot_df = spectra_df.copy()
        if spectra_df.shape[1] > 1:  # the intensity is read from the average
            plot_df[t('Average')] = spectra_df.mean(axis=1)
        settings = vis_utils.default_chart_settings()
        settings['titles']['title'] = name
        fig = px.line(plot_df, color_discrete_sequence=settings['palette'])
        fig.update_layout(dragmode='select', selectdirection='h', height=400)
        if tuple(ranges[name]) != (low, high):
            vis_utils.highlight_range(fig, *ranges[name], opacity=0.2)
        if peak is not None:
            if mode != 'none':  # what is subtracted, under the spectrum the intensity is read from
                base = baselines[name].mean(axis=1)
                fig.add_trace(go.Scatter(x=base.index, y=base, mode='lines', showlegend=False, hoverinfo='skip',
                                         line=dict(dash='dot', width=2, color=fig.data[-1].line.color)))
            lines = [f'I = {peak["intensity"]:,.0f} ({peak["position"]:.0f} cm⁻¹)'.replace(',', ' ')]
            if peak['n'] > 1:
                lines.append(f'RSD {100 * peak["rsd"]:.1f} % ({vis_utils.rsd_interval(peak["rsd"], peak["n"])})')
            if name == 'SERS' and ef is not None:
                lines.insert(0, f'<b>EF = {short(ef)}</b>')
            vis_utils.chart_note(fig, '<br>'.join(lines + [baseline_text]))
        with col:
            vis_utils.show_chart(fig, settings, key=chart_key, selection_mode='box',
                                 on_select=lambda c=chart_key, r=range_key, lo=low, hi=high:
                                 vis_utils.range_from_selection(c, r, lo, hi))
            if peak is None:
                st.warning(t('Selected peak range is empty'))
            elif peak['n'] > 1:
                st.caption(t('Average of {n} spectra. Peak intensity SD: {sd} (RSD {rsd} %)').format(
                    n=peak['n'], sd=f'{peak["sd"]:.0f}', rsd=f'{100 * peak["rsd"]:.1f}'))
    if ef is None:
        return None

    rsd = {name: peak['rsd'] for name, peak in peaks.items() if peak['n'] > 1}
    return peaks['Raman']['intensity'], peaks['SERS']['intensity'], rsd, baseline_text


def build_report(inputs, steps, ef, uncertainty, analyte, peak_baseline=None):
    from core import report

    labels = {'ef_conc_x': 'C = x·10ⁿ mol/dm³, x', 'ef_conc_n': 'n', 'ef_volume': t('Volume of solution [µl]'),
              'ef_wavelength': t('Laser wavelength [nm]'), 'ef_na': 'NA', 'ef_size_x': t('Size x [mm]'),
              'ef_size_y': t('Size y [mm]'), 'ef_development': t('Surface area development coefficient'),
              'ef_coverage': t('The coverage of the surface by the analyte (0-1)'),
              'ef_density': t('Compound density [g/cm³]'), 'ef_molecular_weight': t('Molecular weight [g/mol]'),
              'ef_depth': 'h [mm]', 'ef_i_raman': t('Raman Intensity'), 'ef_i_sers': t('SERS Intensity')}
    rep = report.Report(t('Enhancement Factor (EF) calculator'))
    rep.heading(t('Results'))
    results = {'EF': f'{ef:.2e}'}
    if uncertainty:
        results[t('EF range (90 %)')] = f'{uncertainty["low"]:.2e} – {uncertainty["high"]:.2e}'
    rep.key_values(results)
    rep.heading(t('Parameters'))
    peak = {t('Baseline under the peak'): peak_baseline} if peak_baseline else {}
    rep.key_values({t('Analyte preset'): t(ANALYTE_LABELS[analyte]),
                    **{labels[key]: value for key, value in inputs.items()}, **peak}, label_width=95)
    rep.heading(t('Show calculation step by step'))
    rep.table(pd.DataFrame([(name, value, unit) for name, _, value, unit in steps],
                           columns=[t('Parameter'), t('Value'), '']), index=False)
    if uncertainty:
        names = {'coverage': t('Surface coverage'), 'development': t('Surface development'),
                 'depth': t('Penetration depth'), 'i_sers': t('SERS Intensity'), 'i_raman': t('Raman Intensity')}
        rep.heading(t('Which input changes EF the most'))
        rep.figure(report.range_figure({names[k]: v for k, v in uncertainty['sensitivity'].items()}, ef, 'EF'),
                   width=150)
    rep.text(t('Method: P. Piecyk, A. Kowalska, T. Szymborski, IChF PAN 2020.'), size=8)
    return rep.to_bytes()
