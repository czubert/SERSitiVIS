"""
Enhancement Factor calculator.
Method: 'Enhancement Factor (EF): teoria i praktyka', P. Piecyk, A. Kowalska, T. Szymborski, IChF PAN 2020.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from core import analysis, processing
from vis_helpers import vis_utils
from vis_helpers.i18n import t, choice

SPECTRA_TYPES = ['Raman', 'SERS']

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
    with st.expander(t('Load parameters from a file'), icon=':material/upload_file:'):
        st.file_uploader(t('Upload a parameters file (CSV) downloaded from this page earlier'), type=['csv'],
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

    with cols[1].container(border=True):
        st.markdown(f'##### :material/show_chart: {t("Intensities")}')
        source = choice('radio', t('Intensities'), ['input', 'spectra'], key='ef_source', horizontal=True,
                        label_visibility='collapsed',
                        format_func=lambda s: t('Type in the intensities') if s == 'input'
                        else t('Read them from uploaded spectra'))
        if source == 'spectra':
            intensities = intensities_from_spectra(df)
            if intensities is None:
                return
            i_raman, i_sers = intensities
        else:
            c = st.columns(2)
            i_raman = c[0].number_input(t('Raman Intensity'), 1, 1000000, 1000, 100, key='ef_i_raman')
            i_sers = c[1].number_input(t('SERS Intensity'), 1, 10000000, 60000, 1000, key='ef_i_sers')

    # # Calculation
    n = analysis.num_of_molecules(concentration, volume)
    s_laser = analysis.laser_spot_diameter(wavelength, aperture)
    s0 = analysis.laser_spot_area(s_laser)
    s_platform = size_x * size_y * 10 ** (-6) * development
    n_sers = analysis.n_sers(n, s0, coverage, s_platform)
    v_compound = s0 * depth
    n_raman = analysis.n_raman(s0, depth, density, molecular_weight)
    ef = analysis.enhancement_factor(i_sers, n_sers, i_raman, n_raman)

    with result:
        c = st.columns(4)
        c[0].metric('EF', f'{ef:.1e}', border=True)
        c[1].metric('N SERS', f'{n_sers:.1e}', border=True)
        c[2].metric('N Raman', f'{n_raman:.1e}', border=True)
        c[3].metric('I SERS / I Raman', f'{i_sers / i_raman:.1f}', border=True)

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


def intensities_from_spectra(df):
    """
    Peak intensities read from the uploaded spectra
    :return: (I Raman, I SERS) or None
    """
    if df is None:
        st.warning(t('Upload Raman and SERS spectra in the sidebar'))
        return None

    st.caption(t('Choose which uploaded spectra are Raman and which are SERS. Several spectra of each type '
                 '(e.g. from a map) are averaged. Choose the same band in both, e.g. ~1075 or ~1588 cm⁻¹ for p-MBA.'))
    baseline_correction = st.checkbox(t('Subtract baseline before reading peak intensities'), value=True,
                                      key='ef_baseline')
    degree = st.slider(t('Polynomial degree for baseline correction'), 1, 20, 5, key='ef_baseline_degree',
                       disabled=not baseline_correction)

    spectra = {}
    for col, name in zip(st.columns(2), SPECTRA_TYPES):
        with col:
            label = t('Raman spectra') if name == 'Raman' else t('SERS spectra')
            chosen = st.multiselect(label, list(df.columns), key=f'ef_{name}_spectra')
            if chosen:
                spectra[name] = processing.subtract_baseline(df[chosen], degree) if baseline_correction \
                    else df[chosen]
            else:
                st.warning(t('Choose {name} spectra').format(name=name))

    if len(spectra) < 2:
        return None

    st.caption(t('Tip: drag on the chart to select the peak range.'))
    intensities = {}
    for col, name in zip(st.columns(2), SPECTRA_TYPES):
        spectra_df = spectra[name]
        low, high = vis_utils.spectrum_limits(spectra_df)
        range_key, chart_key = f'ef_{name}_range', f'ef_{name}_chart'

        with col:
            # separate range for each spectrum - the same band is usually shifted by a few cm-1
            label = t('Raman peak range') if name == 'Raman' else t('SERS peak range')
            peak_range = vis_utils.range_slider(label, low, high, key=range_key)

            plot_df = spectra_df.copy()
            if spectra_df.shape[1] > 1:
                plot_df[t('Average')] = spectra_df.mean(axis=1)
            settings = vis_utils.default_chart_settings()
            settings['titles']['title'] = name
            fig = px.line(plot_df, color_discrete_sequence=settings['palette'])
            fig.update_layout(dragmode='select', selectdirection='h', height=400)
            if tuple(peak_range) != (low, high):
                fig.add_vrect(x0=peak_range[0], x1=peak_range[1], line_width=0, fillcolor='gold', opacity=0.2)
            vis_utils.show_chart(fig, settings, key=chart_key, selection_mode='box',
                                 on_select=lambda c=chart_key, r=range_key, lo=low, hi=high:
                                 vis_utils.range_from_selection(c, r, lo, hi))

            peak = analysis.peak_intensity(spectra_df, *peak_range)
            if peak is None:
                st.warning(t('Selected peak range is empty'))
                return None
            intensities[name] = peak['intensity']
            st.markdown(f'$I_{{{name}}} =$ {peak["intensity"]:.0f} {t("at")} {peak["position"]:.0f} cm⁻¹')
            if peak['n'] > 1:
                st.caption(t('Average of {n} spectra. Peak intensity SD: {sd} (RSD {rsd} %)').format(
                    n=peak['n'], sd=f'{peak["sd"]:.0f}', rsd=f'{100 * peak["rsd"]:.1f}'))

    return intensities['Raman'], intensities['SERS']
