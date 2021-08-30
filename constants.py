# TODO should we split it into plural constants?
LABELS = {
    # If no data or at the beggining of the program
    'EMPTY': 'Choose...',
    
    # labels for spectrometers
    'UplSpec': 'Upload "*.txt" spectra',
    'BWTEK': 'BWTEK',
    'RENI': 'Renishaw',
    'WITEC': 'WITec Alpha300 R+',
    'WASATCH': 'Wasatch System',
    'TELEDYNE': 'Teledyne Princeton Instruments',
    'JOBIN': 'Jobin Yvon T64000',
    
    # labels for data visualisation type
    'SINGLE': 'Single spectra',
    'MS': "Mean spectrum",
    'GS': "Grouped spectra",
    'P3D': "Plot 3D",
    
    # labels for plots
    'AV': "Average",
    'BS': "Baseline",
    'RS': "Raman Shift",
    'DS': "Dark Subtracted #1",
    
    # labels for adjusting plots
    'DEG': "Polynominal degree",
    'WINDOW': "Set window for spectra flattening",
    
    'DFS': {
        'ML model grouped spectra': 'Dark Subtracted #1',
        'ML model mean spectra': 'Average'},
    
    # labels for chart and axis
    'FLAT': "Flattened",
    'COR': "Corrected",
    'ORG': "Original spectrum",
    'RAW': "Raw Data",
    'OPT': "Optimised Data",
    'NORM': "Normalized",
    'SHIFT': 'Separate spectra from each other',
    'OPT_S': "Optimised Spectrum",
    
    # for wasatch spectrometer
    'PRCSD': "Processed",
    'TXT': 'txt',
    'CSV': 'csv',
    'IT': 'Integration Time',
    'LP': 'Laser Power',
    'PAT': '-20201009-093705-137238-WP-00702.txt',
    'RAW_WASATCH': 'Raw',
    
    # RMSE types
    'OneP': 'Calculate RSD of "Selected Peak" between different spectra',
    'P2P': 'Calculate RSD of "Peak to Peak ratio" between different different spectra',
    
}
