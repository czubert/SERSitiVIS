import numpy as np
import streamlit as st
from . import enhancement_factor_utils, ef_user_input, vis_utils


def main():
    st.title('Enhancement Factor calculator')

    # # # #
    # # #
    # # First step of calculations and the user input required to calculate it
    #
    st.markdown('## First step of calculations')
    step = st.beta_expander('Show description')
    with step:
        st.markdown('### Calculating the number of molecules ($N$) in the solution')
        st.markdown(r'### <p style="text-align: center;">$$N=N_A \times C \times V$$</p>', unsafe_allow_html=True)
        st.markdown(r'$N$ - Number of particles')
        st.markdown(r'$N_A$ - Avogadro constant $[mol^{-1}]$')
        st.markdown(r'$C$ - Molar concentration $[\frac{mol}{dm^3}]$')
        st.markdown(r'$V$ - Volume $[{dm^3}]$')

    # #  Concentration of analyte in solution (in mol/dm^3
    concentration = ef_user_input.get_concentration()
    
    # # Volume of solution (ml)
    volume = ef_user_input.get_volume()
    
    # # Calculating the number of molecules
    num_molecules = enhancement_factor_utils.num_of_molecules(concentration, volume)

    st.markdown(r'$N =$' + f' {"{:.1e}".format(num_molecules)} $[m^2]$')
    
    # # # #
    # # #
    # # Second step of calculations and the user input required to calculate it
    #
    st.markdown('---')
    st.markdown('## Second step of calculations')
    step = st.beta_expander('Show description')

    with step:
        st.markdown('### Calculating the laser spot ($S_{Laser}$), '
                    'which is the function of wave length and aperture of the lens:')
    
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em">$$S_{Laser}=\frac{1.22 \times \lambda}{NA}$$</p>',
            unsafe_allow_html=True)
        st.markdown(r'$S_{Laser}$ - diameter of the laser spot $[m]$')
        st.markdown(r'$\lambda$ - Laser wavelength $[m]$')
        st.markdown(r'$NA$ - value of numerical aperture, lens dependent')

    cols = st.beta_columns(2)
    with cols[0]:
        # # Laser wavelength in nm
        laser_wave_length = ef_user_input.get_Laser_wave_length()
    with cols[1]:
        # # Lens parameter - Numerical aperture
        lens_params = ef_user_input.get_lens_params()

    # # Calculating the Laser spot
    s_laser = enhancement_factor_utils.cal_size_of_laser_spot(laser_wave_length, lens_params)
    st.markdown(r'$S_{Laser} =$' + f' {"{:.1e}".format(s_laser)} $[m^2]$')

    # # # #
    # # #
    # # Third step of calculations and the user input required to calculate it
    #
    st.markdown('---')
    st.markdown('## Third step of calculations')
    step = st.beta_expander('Show description')

    with step:
        st.markdown('### Calculating the surface area irradiated with the laser ($S_{0}$)')
    
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em">$$S_{0}=\pi \times (\frac{S_{Laser}}{2})^2$$</p>',
            unsafe_allow_html=True)
        st.markdown(r'$S_{0}$ - Surface area of the laser spot $[m^2]$')
        st.markdown(r'$\pi$ - mathematical constant, approximately equal to 3.14159')
        st.markdown(r'$S_{Laser}$ - Laser spot diameter calculated in the previous step $[m^2]$')

    s0_spot_area = np.pi * (s_laser / 2) ** 2
    st.markdown(r'$S_{0} =$' + f' {"{:.1e}".format(s0_spot_area)} $[m^2]$')

    # # # #
    # # #
    # # Fourth step of calculations and the user input required to calculate it
    #
    st.markdown('---')
    st.markdown('## Fourth step of calculations')
    step = st.beta_expander('Show description')

    with step:
        st.markdown('### Determination of the number of molecules per laser irradiated surface ($N_{SERS}$)')
    
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
            r'\frac {N \times S_{Laser}}{S_{Platform}}$$</p>',
            unsafe_allow_html=True)
        # # Arrow
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em; margin-top:-35px; margin-bottom:-55px;">&darr;</p>',
            unsafe_allow_html=True)
        # # Final formula for N_SERS
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em; margin-top:-35px">$$N_{SERS} = '
            r'\frac {N \times S_{Laser} \times coverage}{S_{Platform}}$$</p>',
            unsafe_allow_html=True)
    
        st.markdown(r'$N_{SERS}$ - The number of molecules per laser irradiated surface')
        st.markdown(r'$N_{Laser}$ - $$\frac {N \times S_{Laser}}{S_{Platform}}$$')
        st.markdown(r'$coverage$ - Surface coverage with the particles (e.g. for p-MBA $10^{-6} M$ ~= 10%')
        st.markdown(r'$N$ - Number of particles')
        st.markdown(r'$S_{Laser}$ - Laser spot diameter calculated in the previous step $[m]$')
        st.markdown(r'$S_{Platform}$ - Surface of the SERS platform '
                    r'$\times$ surface area development coefficient (rough surface ~= 2) $[m^2]$')

    # # The area of active surface of the SERS substrate
    s_platform = ef_user_input.get_active_surface_area()
    # # The coverage of the analyte on the surface between 10^-6 and 6*10^-6 ~=10%
    surface_coverage = ef_user_input.get_surface_coverage()

    # n_sers = (num_molecules * s_laser * surface_coverage) / s_platform  # formula version
    n_sers = (num_molecules * s0_spot_area * surface_coverage) / s_platform  # Szymborski use

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
    step = st.beta_expander('Show description')
    with step:
        st.markdown('### Calculation of the volume from which the Raman signal for your compound in solids is recorded')
        st.markdown(r'### <p style="text-align: center;">$$V_{compound}=S_0 \times h$$</p>', unsafe_allow_html=True)
        st.markdown(r'$V_{compound}$ - The volume of your chemical compound crystal subjected to laser illumination')
        st.markdown(r'$S_0$ - Surface area of the laser spot $[m^2]$')
        st.markdown(r'$h$ - Depth into which the laser penetrates the chemical compound in crystalline '
                    r'form (in the case of p-MBA we assume 2 mm)')

    penetration_depth = ef_user_input.get_penetration_depth()
    v_compound = s0_spot_area * penetration_depth

    st.markdown(r'$V_{compound} =$' + f' {"{:.1e}".format(v_compound)} $[m^3]$')

    st.markdown('---')

    # # # #
    # # #
    # # Sixth step of calculations and the user input required to calculate it
    #
    st.markdown('## Sixth step of calculations')
    step = st.beta_expander('Show description')
    with step:
        st.markdown(r'#### Determining the number of p-MBA molecules from which the Raman signal ($N_{Raman}$) comes')
    
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
            r'Lastly, The number of molecules irradiated during the recording of the Raman spectrum (&N_{Raman}&) is obtained by multiplying the number of moles by the Avogadro constant:')
        st.markdown(r'### <p style="text-align: center;">$$N_{Raman}= n_{compound}\times N_A$$</p>',
                    unsafe_allow_html=True)
        st.markdown(r'$N_{Raman}$ - The number of molecules irradiated during the recording of the Raman spectrum')
        st.markdown(r'$n_{compound}$ - Mass of the irradiated crystal $[mol]$')
        st.markdown(r'$N_A$ - Avogadro constant $[mol^{-1}]$')

    # # Molecular weight
    compound_density = ef_user_input.get_compound_density()
    compound_molecular_weight = ef_user_input.get_molecular_weight()

    n_raman = enhancement_factor_utils.cal_n_raman(v_compound, compound_density, compound_molecular_weight)

    st.markdown(r'$N_{Raman} =$' + f' {"{:.1e}".format(n_raman)}')

    st.markdown('---')

    # # # #
    # # #
    # # Final, seventh, step of calculations and the user input required to calculate it
    #
    st.markdown('## seventh step of calculations')
    step = st.beta_expander('Show description')
    with step:
        st.markdown('### Calculating the Enhancement Factor')
        st.markdown(
            r'### <p style="text-align: center;">$$EF=\frac{I_{SERS}}{N_{SERS}} \times \frac{N_{Raman}}{I_{Raman}}$$</p>',
            unsafe_allow_html=True)
        st.markdown(
            r'$I_{SERS}$ - SERS signal (particular peak) of your compound adsorbed on the surface of the SERS platform')
        st.markdown(r'$N_{SERS}$ - The number of molecules irradiated during the recording of the SERS spectrum')
        st.markdown(r'$I_{Raman}$ - Raman signal (particular peak) of you compound')
        st.markdown(r'$N_{Raman}$ - The number of molecules irradiated during the recording of the Raman spectrum')

    # # SERS intensity and Raman Intensity
    # TODO wykorzystać Charza pomysł na wybieranie maksa z zakresu, gdyby ktoś chciał, żeby mu automatycznie policzyło
    i_sers, i_raman = ef_user_input.get_laser_intensities()

    enhancement_factor = (i_sers / n_sers) * (n_raman / i_raman)

    st.markdown(r'$EF =$' + f' {"{:.1e}".format(enhancement_factor)}')

    st.markdown('---')
