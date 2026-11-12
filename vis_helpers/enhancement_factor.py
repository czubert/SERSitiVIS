import plotly.express as px
import streamlit as st

from core import analysis, processing
from visualisation.draw import fig_layout
from . import ef_utils
from . import vis_utils


def main(df):
    """
    :param df: DataFrame with uploaded spectra (shared data) or None
    """
    st.title('Enhancement Factor calculator')

    # # # #
    # # #
    # # First step of calculations and the user input required to calculate it
    #
    st.markdown('## First step of calculations')
    st.markdown('### Calculating the number of molecules ($N$) in the solution')
    step = st.expander('Show description')
    with step:
        st.markdown(r'### <p style="text-align: center;">$$N=N_A \times C \times V$$</p>', unsafe_allow_html=True)
        st.markdown(r'$N$ - Number of particles')
        st.markdown(r'$N_A$ - Avogadro constant $[mol^{-1}]$')
        st.markdown(r'$C$ - Molar concentration $[\frac{mol}{dm^3}]$')
        st.markdown(r'$V$ - Volume $[{dm^3}]$')

    # #  Concentration of analyte in solution (in mol/dm^3
    concentration = ef_utils.get_concentration()

    # # Volume of solution (ml)
    volume = ef_utils.get_volume()

    # # Calculating the number of molecules
    num_molecules = analysis.num_of_molecules(concentration, volume)

    st.markdown(r'$N =$' + f' {"{:.1e}".format(num_molecules)}')

    # # # #
    # # #
    # # Second step of calculations and the user input required to calculate it
    #
    st.markdown('---')
    st.markdown('## Second step of calculations')
    st.markdown('### Calculating the laser spot ($S_{Laser}$), '
                'which is the function of wave length and aperture of the lens:')
    step = st.expander('Show description')

    with step:
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em">$$S_{Laser}=\frac{1.22 \times \lambda}{NA}$$</p>',
            unsafe_allow_html=True)
        st.markdown(r'$S_{Laser}$ - diameter of the laser spot $[m]$')
        st.markdown(r'$\lambda$ - Laser wavelength $[m]$')
        st.markdown(r'$NA$ - value of numerical aperture, lens dependent')

    cols = st.columns(2)
    with cols[0]:
        # # Laser wavelength in nm
        laser_wave_length = ef_utils.get_laser_wave_length()
    with cols[1]:
        # # Lens parameter - Numerical aperture
        lens_params = ef_utils.get_lens_params()

    # # Calculating the Laser spot
    s_laser = analysis.laser_spot_diameter(laser_wave_length, lens_params)
    st.markdown(r'$S_{Laser} =$' + f' {"{:.1e}".format(s_laser)} $[m]$')

    # # # #
    # # #
    # # Third step of calculations and the user input required to calculate it
    #
    st.markdown('---')
    st.markdown('## Third step of calculations')
    st.markdown('### Calculating the surface area irradiated with the laser ($S_{0}$)')
    step = st.expander('Show description')

    with step:
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em">$$S_{0}=\pi \times (\frac{S_{Laser}}{2})^2$$</p>',
            unsafe_allow_html=True)
        st.markdown(r'$S_{0}$ - Surface area of the laser spot $[m^2]$')
        st.markdown(r'$\pi$ - mathematical constant, approximately equal to 3.14159')
        st.markdown(r'$S_{Laser}$ - Laser spot diameter calculated in the previous step $[m]$')

    s0_spot_area = analysis.laser_spot_area(s_laser)
    st.markdown(r'$S_{0} =$' + f' {"{:.1e}".format(s0_spot_area)} $[m^2]$')

    # # # #
    # # #
    # # Fourth step of calculations and the user input required to calculate it
    #
    st.markdown('---')
    st.markdown('## Fourth step of calculations')
    st.markdown('### Determination of the number of molecules per laser irradiated surface ($N_{SERS}$)')
    step = st.expander('Show description')

    with step:
        # # Basic formula for N_SERS
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em">$$N_{SERS} = N_{Laser} \times coverage$$</p>',
            unsafe_allow_html=True)
        # # Arrow
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em; margin-top:-35px; margin-bottom:-55px;">&darr;</p>',
            unsafe_allow_html=True)
        # # Formula for N_LASER
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em; margin-top:-35px">$$N_{Laser} = '
            r'\frac {N \times S_{0}}{S_{Platform}}$$</p>',
            unsafe_allow_html=True)
        # # Arrow
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em; margin-top:-35px; margin-bottom:-55px;">&darr;</p>',
            unsafe_allow_html=True)
        # # Final formula for N_SERS
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em; margin-top:-35px">$$N_{SERS} = '
            r'\frac {N \times S_{0} \times coverage}{S_{Platform}}$$</p>',
            unsafe_allow_html=True)

        st.markdown(r'$N_{SERS}$ - The number of molecules per laser irradiated surface')
        st.markdown(r'$N_{Laser}$ - The number of molecules within the laser spot')
        st.markdown(r'$coverage$ - Surface coverage with the particles (e.g. for p-MBA $10^{-6} M$ ~= 10%)')
        st.markdown(r'$N$ - Number of particles')
        st.markdown(r'$S_{0}$ - Surface area of the laser spot calculated in the previous step $[m^2]$')
        st.markdown(r'$S_{Platform}$ - Surface of the SERS platform '
                    r'$\times$ surface area development coefficient (rough surface ~= 2) $[m^2]$')

    # # The area of active surface of the SERS substrate
    s_platform = ef_utils.get_active_surface_area()
    # # The coverage of the analyte on the surface between 10^-6 and 6*10^-6 ~=10%
    surface_coverage = ef_utils.get_surface_coverage()

    n_sers = analysis.n_sers(num_molecules, s0_spot_area, surface_coverage, s_platform)

    # TODO delete after checking the results
    # st.markdown(f'num_molecules: {"{:.1e}".format(num_molecules)}')
    # st.markdown(f's_laser: {"{:.1e}".format(s_laser)}')
    # st.markdown(f'surface_coverage: {"{:.1e}".format(surface_coverage)}')
    # st.markdown(f's_platform: {"{:.1e}".format(s_platform)}')

    st.markdown(r'$N_{SERS} =$' + f' {"{:.1e}".format(n_sers)}')
    st.markdown('---')

    # # # #
    # # #
    # # Fifth step of calculations and the user input required to calculate it
    #
    st.markdown('## Fifth step of calculations')
    st.markdown('### Calculation of the volume from which the Raman signal for your compound in solids is recorded')
    step = st.expander('Show description')
    with step:
        st.markdown(r'### <p style="text-align: center;">$$V_{compound}=S_0 \times h$$</p>', unsafe_allow_html=True)
        st.markdown(r'$V_{compound}$ - The volume of your chemical compound crystal subjected to laser illumination')
        st.markdown(r'$S_0$ - Surface area of the laser spot $[m^2]$')
        st.markdown(r'$h$ - Depth into which the laser penetrates the chemical compound in crystalline '
                    r'form (in the case of p-MBA we assume 2 mm)')

    penetration_depth = ef_utils.get_penetration_depth()
    v_compound = s0_spot_area * penetration_depth

    st.markdown(r'$V_{compound} =$' + f' {"{:.1e}".format(v_compound)} $[m^3]$')

    st.markdown('---')

    # # # #
    # # #
    # # Sixth step of calculations and the user input required to calculate it
    #
    st.markdown('## Sixth step of calculations')
    st.markdown(r'### Determining the number of p-MBA molecules from which the Raman signal ($N_{Raman}$) comes')
    step = st.expander('Show description')
    with step:
        st.markdown('---')

        st.markdown(r'Firstly, the mass of the irradiated crystal is determined from the compound density:')
        st.markdown(r'### <p style="text-align: center;">$$m_{compound}=d_{compound} \times V_{compound}$$</p>',
                    unsafe_allow_html=True)
        st.markdown(r'$m_{compound}$ - Mass of the irradiated crystal $[g]$')
        st.markdown(r'$d_{compound}$ - density of the chemical compound$[\frac{g}{cm^3}]$')
        st.markdown(
            r'$V_{compound}$ - The volume of your chemical compound crystal subjected to laser illumination $[m^3]$')

        st.markdown('---')

        st.markdown(r'Secondly, from the molar mass, the number of moles is calculated:')
        st.markdown(r'### <p style="text-align: center;">$$n_{compound}= \frac{m_{compound}}{M_{compound}}$$</p>',
                    unsafe_allow_html=True)
        st.markdown(r'$n_{compound}$ - Number of moles of the irradiated crystal $[mol]$')
        st.markdown(r'$m_{compound}$ - Mass of the irradiated crystal $[g]$')
        st.markdown(r'$M_{compound}$ - Molecular weight of the chemical compound $[\frac{g}{mol}]$')

        st.markdown('---')

        st.markdown(
            r'Lastly, The number of molecules irradiated during the recording of the Raman spectrum ($N_{Raman}$) is obtained by multiplying the number of moles by the Avogadro constant:')
        st.markdown(r'### <p style="text-align: center;">$$N_{Raman}= n_{compound}\times N_A$$</p>',
                    unsafe_allow_html=True)
        st.markdown(r'$N_{Raman}$ - The number of molecules irradiated during the recording of the Raman spectrum')
        st.markdown(r'$n_{compound}$ - Number of moles of the irradiated crystal $[mol]$')
        st.markdown(r'$N_A$ - Avogadro constant $[mol^{-1}]$')

    # # Molecular weight
    compound_density = ef_utils.get_compound_density()
    compound_molecular_weight = ef_utils.get_molecular_weight()

    n_raman = analysis.n_raman(s0_spot_area, penetration_depth, compound_density, compound_molecular_weight)

    st.markdown(r'$N_{Raman} =$' + f' {"{:.1e}".format(n_raman)}')

    st.markdown('---')

    # # # #
    # # #
    # # Final, seventh, step of calculations and the user input required to calculate it
    #
    st.markdown('## Seventh step of calculations')
    st.markdown('### Calculating the Enhancement Factor')
    step = st.expander('Show description')
    with step:
        st.markdown(
            r'### <p style="text-align: center;">$$EF=\frac{I_{SERS}}{N_{SERS}} \times \frac{N_{Raman}}{I_{Raman}}$$</p>',
            unsafe_allow_html=True)
        st.markdown(
            r'$I_{SERS}$ - SERS signal (particular peak) of your compound adsorbed on the surface of the SERS platform')
        st.markdown(r'$N_{SERS}$ - The number of molecules irradiated during the recording of the SERS spectrum')
        st.markdown(r'$I_{Raman}$ - Raman signal (particular peak) of you compound')
        st.markdown(r'$N_{Raman}$ - The number of molecules irradiated during the recording of the Raman spectrum')

    # # SERS intensity and Raman Intensity

    intensities_options = {'input': 'Input the intensities for Raman and SERS',
                           'from_spec': 'Get Raman and SERS intensities from their spectra'}

    intensities_radio = st.radio('Choose whether you want to input intensities or get the values from spectra',
                                 ['input', 'from_spec'],
                                 format_func=intensities_options.get
                                 )

    if intensities_radio == 'input':
        i_sers, i_raman = ef_utils.get_laser_intensities()

    else:
        if df is None:
            st.warning('Upload Raman and SERS spectra in the sidebar')
            return

        with st.expander("Customize your chart"):
            plot_palette, plot_template = vis_utils.get_chart_vis_properties()

        st.info('Choose which uploaded spectra are Raman and which are SERS. Several spectra of each type '
                '(e.g. from a map) are averaged. Choose the same band in both, e.g. ~1075 or ~1588 cm⁻¹ for p-MBA.')

        baseline_correction = st.checkbox('Subtract baseline before reading peak intensities', value=True)
        if baseline_correction:
            degree = st.slider('Polynomial degree for baseline correction', 1, 20, 5, key='ef_baseline_degree')

        spectra = {}
        cols = st.columns(2)
        for col, name in zip(cols, ['Raman', 'SERS']):
            with col:
                chosen = st.multiselect(f'{name} spectra', list(df.columns), key=f'ef_{name}_spectra')
                if not chosen:
                    st.warning(f'Choose {name} spectra')
                    continue
                spectra[name] = processing.subtract_baseline(df[chosen], degree) if baseline_correction                     else df[chosen]

        if len(spectra) < 2:
            return

        intensities = {}
        bg_color = 'yellow'
        cols = st.columns(2)
        for col, name in zip(cols, ['Raman', 'SERS']):
            spectra_df = spectra[name]
            plot_x_min, plot_x_max = int(spectra_df.index.min()), int(spectra_df.index.max())

            with col:
                # separate range for each spectrum - the same band is usually shifted by a few cm-1
                peak_range = st.slider(f'{name} peak range ({bg_color})',
                                       min_value=plot_x_min,
                                       max_value=plot_x_max,
                                       value=(plot_x_min, plot_x_max),
                                       key=f'ef_{name}_range')

                plot_df = spectra_df.copy()
                if spectra_df.shape[1] > 1:
                    plot_df['Average'] = spectra_df.mean(axis=1)
                fig = px.line(plot_df, color_discrete_sequence=plot_palette)
                fig_layout(plot_template, fig, plots_colorscale=plot_palette)
                fig.update_xaxes(range=[plot_x_min, plot_x_max])

                if tuple(peak_range) != (plot_x_min, plot_x_max):
                    fig.add_vline(x=peak_range[0], line_dash="dash")
                    fig.add_vline(x=peak_range[1], line_dash="dash")
                    fig.add_vrect(x0=peak_range[0], x1=peak_range[1], line_width=0, fillcolor=bg_color, opacity=0.15)

                st.plotly_chart(fig, width='stretch')

                peak = analysis.peak_intensity(spectra_df, *peak_range)
                if peak is None:
                    st.warning('Selected peak range is empty')
                    return

                intensities[name] = peak['intensity']
                st.markdown(f'$I_{{{name}}} =$ {peak["intensity"]:.0f} at {peak["position"]:.0f} cm⁻¹')
                if peak['n'] > 1:
                    st.caption(f'Average of {peak["n"]} spectra. Peak intensity SD: {peak["sd"]:.0f} '
                               f'(RSD {100 * peak["rsd"]:.1f} %)')

        i_raman, i_sers = intensities['Raman'], intensities['SERS']

    ef = analysis.enhancement_factor(i_sers, n_sers, i_raman, n_raman)

    st.markdown(r'$EF =$' + f' {"{:.1e}".format(ef)}')

    st.markdown('---')
