import streamlit as st
from . import enhancement_factor_utils, ef_user_input, vis_utils


def main():
    st.header('Enhancement Factor calculator')
    
    # # # #
    # # #
    # # First step of calculations and the user input required to calculate it
    #
    st.markdown('### First step of calculations')
    first_step = st.beta_expander('Show description')
    with first_step:
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
    
    st.markdown(f'The number of molecules: {"{:.1e}".format(num_molecules)}')
    
    # # # #
    # # #
    # # Second step of calculations and the user input required to calculate it
    #
    st.markdown('---')
    st.markdown('### Second step of calculations')
    second_step = st.beta_expander('Show description')
    
    with second_step:
        st.markdown('### Calculating the laser spot ($S_{Laser}$), '
                    'which is the function of wave length and aperture of the lens:')
        
        st.markdown(
            r'### <p style="text-align: center;font-size:1.15em">$$S_{Laser}=\frac{1.22 \times \lambda}{NA}$$</p>',
            unsafe_allow_html=True)
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
    laser_spot_size = enhancement_factor_utils.cal_size_of_laser_spot(laser_wave_length, lens_params)
    st.markdown(f'The laser spot size: {round(laser_spot_size, 8)} $[m]$')
    
    # # # #
    # # #
    # # Third step of calculations and the user input required to calculate it
    #
    st.markdown('---')
    st.markdown('### Third step of calculations')
    second_step = st.beta_expander('Show description')
    
    with second_step:
        st.markdown('### calculation of the surface area irradiated with the laser ($S_{0}$)')
        
        st.markdown(r'### <p style="text-align: center;font-size:1.15em">$$S_{0}=\pi \times \frac{S_{Laser}}{2}$$</p>',
                    unsafe_allow_html=True)
        st.markdown(r'$\lambda$ - Laser wavelength $[m]$')
        st.markdown(r'$NA$ - value of numerical aperture, lens dependent')
    
    # # The area of active surface of the SERS substrate
    active_area = ef_user_input.get_active_surface_area()
    
    # # The coverage of the analyte on the surface between 10^-6 and 6*10^-6 ~=10%
    surface_coverage = ef_user_input.get_surface_coverage()
    
    # # SERS intensity and Raman Intensity
    i_sers, i_raman = ef_user_input.get_laser_intensities()
    
    # # Molecular weight
    molecular_weight = ef_user_input.get_molecular_weight()
    
    # # #
    # # Calculating Enhancement Factor
    #
    
    laser_spot_area = enhancement_factor_utils.cal_laser_spot_surface_area(laser_spot_size)
    
    n_sers = enhancement_factor_utils.cal_n_sers(active_area, laser_spot_area, num_molecules, surface_coverage)
    n_raman = enhancement_factor_utils.cal_n_raman(laser_spot_area)
    
    enhancement_factor = (i_sers / n_sers) * (n_raman / i_raman)
    st.write(enhancement_factor)
    st.write(enhancement_factor / 1e+8)
