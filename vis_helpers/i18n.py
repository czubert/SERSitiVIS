"""
Translations. English is the default; texts are written in English in the code and wrapped in t().
Polish translations live in PL. A missing translation falls back to English (a test checks that none is missing).
"""
import base64

import streamlit as st

LANGUAGES = {'en': 'English', 'pl': 'Polski', 'de': 'Deutsch', 'uk': 'Українська'}
LANG_KEY = 'lang'


def lang():
    return st.session_state.get(LANG_KEY, 'en')


def t(text):
    return translations().get(lang(), {}).get(text, text)


def translations():
    from vis_helpers.lang_de import DE
    from vis_helpers.lang_uk import UK
    return {'pl': PL, 'de': DE, 'uk': UK}


# Flags as images - emoji flags are shown as letters ("GB", "PL") in browsers on Windows
FLAGS = {
    'en': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 30"><clipPath id="s"><path d="M0,0 v30 h60 v-30 z"/>'
          '</clipPath><clipPath id="t"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath>'
          '<g clip-path="url(#s)"><path d="M0,0 v30 h60 v-30 z" fill="#012169"/><path d="M0,0 L60,30 M60,0 L0,30" '
          'stroke="#fff" stroke-width="6"/><path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#t)" stroke="#C8102E" '
          'stroke-width="4"/><path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/><path d="M30,0 v30 '
          'M0,15 h60" stroke="#C8102E" stroke-width="6"/></g></svg>',
    'pl': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 10"><rect width="16" height="5" fill="#fff"/>'
          '<rect y="5" width="16" height="5" fill="#DC143C"/></svg>',
    'de': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 5 3"><rect width="5" height="1" fill="#000"/>'
          '<rect y="1" width="5" height="1" fill="#DD0000"/><rect y="2" width="5" height="1" fill="#FFCE00"/></svg>',
    'uk': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2"><rect width="3" height="1" fill="#0057B7"/>'
          '<rect y="1" width="3" height="1" fill="#FFD700"/></svg>',
}


def _flags_css():
    def data_uri(svg):
        return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()

    option = '.st-key-_lang_widget [data-testid="stRadioGroup"] > div'
    rules = [
        # hide radio circles and texts (texts stay for screen readers), show flags instead
        f'{option} [data-testid="stRadioOption"] > div > div:first-child {{display: none;}}',
        f'{option} [data-testid="stMarkdownContainer"] p {{font-size: 0; line-height: 0; margin: 0;}}',
        f'{option} [data-testid="stMarkdownContainer"] p::before {{content: ""; display: inline-block; width: 36px; '
        f'height: 24px; background-size: 100% 100%; border-radius: 3px; box-shadow: 0 0 0 1px #9aa3ad;}}',
        f'{option} [data-testid="stRadioOption"]:not([data-selected="true"]) {{opacity: 0.4;}}',
        f'{option} [data-testid="stRadioOption"]:hover {{opacity: 1;}}',
    ]
    for i, code in enumerate(LANGUAGES, start=1):
        rules.append(f'{option}:nth-child({i}) [data-testid="stMarkdownContainer"] p::before '
                     f'{{background-image: url("{data_uri(FLAGS[code])}");}}')
    return '<style>' + ' '.join(rules) + '</style>'


def language_selector():
    """Language switch (flags) in the sidebar. Kept in a plain session_state key, so it survives page changes."""
    st.session_state.setdefault(LANG_KEY, 'en')
    st.session_state.setdefault('_lang_widget', lang())

    def on_change():
        st.session_state[LANG_KEY] = st.session_state['_lang_widget']

    st.html(_flags_css())
    st.sidebar.radio('Language', list(LANGUAGES), format_func=LANGUAGES.get, key='_lang_widget',
                     on_change=on_change, horizontal=True, label_visibility='collapsed')
    st.sidebar.caption(t('English is the original version, other languages are translated by AI.'))


def choice(widget, label, options, key, format_func, container=None, **kwargs):
    """
    st.selectbox / st.radio with translated option labels.
    Streamlit remembers a choice by its displayed text, so after a language change the old text would not match.
    Every language gets its own widget, the chosen value is kept in a plain session_state key.
    :param widget: 'selectbox' or 'radio'
    :return: chosen option
    """
    container = container or st
    store = f'_{key}'
    widget_key = key if lang() == 'en' else f'{key}__{lang()}'
    if st.session_state.get(store) not in options:
        st.session_state[store] = options[0]
    if st.session_state.get(widget_key) not in options:
        st.session_state[widget_key] = st.session_state[store]

    extra_callback = kwargs.pop('on_change', None)

    def on_change():
        st.session_state[store] = st.session_state[widget_key]
        if extra_callback:
            extra_callback()

    labels = {option: format_func(option) for option in options}  # translated now, in the current language
    getattr(container, widget)(label, options, key=widget_key, format_func=labels.get, on_change=on_change,
                               **kwargs)
    return st.session_state[store]


PL = {
    'Clustering needs at least 3 spectra.': 'Klastrowanie wymaga co najmniej 3 widm.',
    'Chart: colour = cluster found by the algorithm, marker shape = your group.': 'Wykres: kolor = klaster znaleziony przez algorytm, kształt punktu = Twoja grupa.',
    # reports
    'Create PDF report': 'Utwórz raport PDF',
    'Creating report...': 'Tworzenie raportu...',
    'Download report (PDF)': 'Pobierz raport (PDF)',
    'Files': 'Pliki',
    'Parameters': 'Parametry',
    'LOD/LOQ from the fit: 3.3·SD(residuals)/slope and 10·SD/slope (ICH Q2). From blank spectra: '
    '3·SD(blank)/slope and 10·SD/slope.':
        'LOD/LOQ z dopasowania: 3,3·SD(reszt)/nachylenie i 10·SD/nachylenie (ICH Q2). Ze ślepej próby: '
        '3·SD(ślepej próby)/nachylenie i 10·SD/nachylenie.',

    # navigation
    'Start': 'Start',
    'Visualisation': 'Wizualizacja',
    'RSD': 'RSD',
    'Enhancement Factor': 'Współczynnik EF',
    'PCA': 'PCA',

    # start page
    'Fast and easy processing and visualisation of Raman and SERS spectra':
        'Szybka i prosta obróbka oraz wizualizacja widm Ramana i SERS',
    'Upload spectra': 'Wgraj widma',
    'Drop *.txt or *.csv files in the sidebar. The spectrometer type is detected automatically.':
        'Upuść pliki *.txt lub *.csv w panelu bocznym. Typ spektrometru rozpoznawany jest automatycznie.',
    'Choose analysis': 'Wybierz analizę',
    'Visualise and process spectra, check reproducibility (RSD), calculate the Enhancement Factor or run PCA.':
        'Wizualizuj i obrabiaj widma, sprawdź powtarzalność (RSD), policz współczynnik wzmocnienia (EF) '
        'lub wykonaj PCA.',
    'Download results': 'Pobierz wyniki',
    'Export charts (PNG, SVG) and processed data (CSV).':
        'Eksportuj wykresy (PNG, SVG) i przetworzone dane (CSV).',
    'Try with example data': 'Wypróbuj na przykładowych danych',
    'Supported spectrometers': 'Obsługiwane spektrometry',
    'other text tables': 'inne tabele tekstowe',
    'Need SERS substrates?': 'Potrzebujesz podłoży SERS?',
    'SERSitive makes reproducible silver and gold SERS substrates.':
        'SERSitive produkuje powtarzalne srebrne i złote podłoża SERS.',
    'Visit SERSitive': 'Odwiedź SERSitive',
    'Feedback and questions': 'Uwagi i pytania',

    # sidebar / data
    'Data': 'Dane',
    'Renishaw WiRE (*.wdf)': 'Renishaw WiRE (*.wdf)',
    'Galactic / Thermo (*.spc)': 'Galactic / Thermo (*.spc)',
    'JCAMP-DX (*.jdx, *.dx)': 'JCAMP-DX (*.jdx, *.dx)',
    'No XY spectrum found in the JCAMP file (peak tables and multi-block files are not supported)':
        'W pliku JCAMP nie ma widma XY (tabele pików i pliki wieloblokowe nie są obsługiwane)',
    'Spectrometer type is detected automatically. You can upload files from different spectrometers at once. '
    'Formats: *.txt, *.csv, Renishaw *.wdf, Galactic *.spc, JCAMP-DX *.jdx.':
        'Typ spektrometru rozpoznawany jest automatycznie. Możesz wgrać naraz pliki z różnych spektrometrów. '
        'Formaty: *.txt, *.csv, Renishaw *.wdf, Galactic *.spc, JCAMP-DX *.jdx.',
    'Spectrometer type is detected automatically. You can upload files from different spectrometers at once.':
        'Typ spektrometru rozpoznawany jest automatycznie. Możesz wgrać naraz pliki z różnych spektrometrów.',
    '...or try example data': '...lub wypróbuj przykładowe dane',
    'File format': 'Format pliku',
    'Change it only if a file is read incorrectly.': 'Zmień tylko, jeśli plik wczytuje się niepoprawnie.',
    'Auto-detect': 'Rozpoznaj automatycznie',
    'Map (X, Y, Raman Shift, Intensity)': 'Mapa (X, Y, przesunięcie Ramana, intensywność)',
    'Text table (Renishaw, WITec, Jobin Yvon, Teledyne, other)':
        'Tabela tekstowa (Renishaw, WITec, Jobin Yvon, Teledyne, inne)',
    'Loaded {spectra} spectra from {files} files': 'Wczytane widma: {spectra}, pliki: {files}',
    'File': 'Plik',
    'Format': 'Format',
    'Spectra': 'Widma',
    'Raman Shift: {low} – {high} cm⁻¹, {points} points': 'Przesunięcie Ramana: {low} – {high} cm⁻¹, {points} punktów',
    'Clear data': 'Wyczyść dane',
    'Spectra do not share a common Raman Shift range - upload them separately.':
        'Widma nie mają wspólnego zakresu przesunięcia Ramana - wgraj je osobno.',
    'Reading files...': 'Wczytywanie plików...',
    'Upload spectra in the sidebar (or choose example data)':
        'Wgraj widma w panelu bocznym (lub wybierz przykładowe dane)',

    # reader errors
    'File is empty': 'Plik jest pusty',
    'No spectrum found in the file': 'W pliku nie znaleziono widma',
    'Could not read the file': 'Nie udało się odczytać pliku',
    'Could not find columns with numbers': 'Nie znaleziono kolumn z liczbami',
    'Expected at least two columns: Raman Shift and intensity':
        'Oczekiwano co najmniej dwóch kolumn: przesunięcie Ramana i intensywność',
    'No intensity column found': 'Nie znaleziono kolumny z intensywnością',
    'BWTEK data header (Pixel; ... Raman Shift ...) not found':
        'Nie znaleziono nagłówka danych BWTEK (Pixel; ... Raman Shift ...)',
    'Wasatch data header (Pixel,Wavelength,Wavenumber...) not found':
        'Nie znaleziono nagłówka danych Wasatch (Pixel,Wavelength,Wavenumber...)',
    'Expected 5 columns: pixel, wavelength, wavenumber, processed, raw':
        'Oczekiwano 5 kolumn: piksel, długość fali, liczba falowa, przetworzone, surowe',

    # visualisation
    'Chart type': 'Typ wykresu',
    'Single spectrum': 'Pojedyncze widmo',
    'Mean spectrum': 'Widmo średnie',
    'Grouped spectra': 'Widma zgrupowane',
    '3D plot': 'Wykres 3D',
    'Spectrum': 'Widmo',
    'English is the original version, other languages are translated by AI.':
        'Wersja oryginalna to angielska, pozostałe języki przetłumaczyła AI.',
    'Previous spectrum': 'Poprzednie widmo',
    'Next spectrum': 'Następne widmo',
    'Range': 'Zakres',
    'Raman Shift range [cm⁻¹]': 'Zakres przesunięcia Ramana [cm⁻¹]',
    'Separate spectra from each other': 'Rozsuń widma',
    'Processing': 'Obróbka',
    'Baseline correction and smoothing': 'Korekta linii bazowej i wygładzanie',
    'Same settings for all spectra': 'Te same ustawienia dla wszystkich widm',
    'Polynomial degree': 'Stopień wielomianu',
    'Higher degree follows the background more closely, but may cut into broad peaks.':
        'Wyższy stopień lepiej dopasowuje się do tła, ale może „zjadać” szerokie piki.',
    'Smoothing window': 'Okno wygładzania',
    'Number of points averaged. 1 = no smoothing.': 'Liczba uśrednianych punktów. 1 = bez wygładzania.',
    'Normalize (0-1)': 'Normalizuj (0-1)',
    'Show baseline and intermediate steps': 'Pokaż linię bazową i kroki pośrednie',
    'Average': 'Średnia',
    'Baseline': 'Linia bazowa',
    'Baseline corrected': 'Po korekcie linii bazowej',
    'Baseline corrected + smoothed': 'Po korekcie i wygładzeniu',
    'Chart appearance': 'Wygląd wykresu',
    'Remove spikes (cosmic rays)': "Usuń spike'i (promienie kosmiczne)",
    'Spike threshold': "Próg spike'ów",
    'In units of noise. Lower = more points treated as spikes.':
        "W jednostkach szumu. Mniej = więcej punktów uznanych za spike'i.",
    'Spike points replaced: {n}': "Zastąpione punkty spike'ów: {n}",
    'Baseline correction': 'Korekta linii bazowej',
    'Baseline method': 'Metoda linii bazowej',
    'Polynomial (ModPoly)': 'Wielomian (ModPoly)',
    'arPLS (strong fluorescence background)': 'arPLS (silne tło fluorescencyjne)',
    'SNIP (peak clipping)': 'SNIP (obcinanie pików)',
    'Smoothness of the baseline (λ)': 'Gładkość linii bazowej (λ)',
    'Higher = stiffer, flatter baseline.': 'Więcej = sztywniejsza, bardziej płaska linia bazowa.',
    'Half window [cm⁻¹]': 'Połowa okna [cm⁻¹]',
    'Smoothing': 'Wygładzanie',
    'Smoothing method': 'Metoda wygładzania',
    'Moving average': 'Średnia krocząca',
    'Savitzky-Golay (keeps peak heights)': 'Savitzky-Golay (zachowuje wysokości pików)',
    'Number of points. Savitzky-Golay uses an odd number.': 'Liczba punktów. Savitzky-Golay używa liczby nieparzystej.',
    'Normalization': 'Normalizacja',
    'None': 'Brak',
    'Min-max (0-1)': 'Min-max (0-1)',
    'Maximum = 1': 'Maksimum = 1',
    'Area = 1': 'Pole = 1',
    'Vector (Euclidean norm = 1)': 'Wektorowa (norma euklidesowa = 1)',
    'SNV (mean 0, SD 1)': 'SNV (średnia 0, SD 1)',
    'Reference peak = 1 (internal standard)': 'Pik odniesienia = 1 (wzorzec wewnętrzny)',
    'Reference peak range': 'Zakres piku odniesienia',
    'Smoothed': 'Wygładzone',
    'Peaks': 'Piki',
    'Raman Shift [cm⁻¹]': 'Przesunięcie Ramana [cm⁻¹]',
    'Find and label peaks': 'Znajdź i podpisz piki',
    'Sensitivity - minimal peak prominence [%]': 'Czułość - minimalna wybitność piku [%]',
    'How much a peak must rise above its surroundings, in % of the spectrum intensity range. Lower = more peaks.':
        'O ile pik musi wznosić się ponad otoczenie, w % zakresu intensywności widma. Mniej = więcej pików.',
    'Minimal distance between peaks [cm⁻¹]': 'Minimalna odległość między pikami [cm⁻¹]',
    'Maximal number of labels per spectrum': 'Maksymalna liczba podpisów na widmo',
    'Intensity': 'Intensywność',
    'Prominence': 'Wybitność',
    'FWHM [cm⁻¹]': 'FWHM [cm⁻¹]',
    'Intensities include the separation shift of the chart.': 'Intensywności zawierają przesunięcie rozsuniętych widm.',
    'Download peaks (CSV)': 'Pobierz piki (CSV)',
    'Raman Shift [cm<sup>-1</sup>]': 'Przesunięcie Ramana [cm<sup>-1</sup>]',
    'Intensity [a.u.]': 'Intensywność [j.u.]',
    'Colour palette': 'Paleta kolorów',
    'Reversed colours': 'Odwróć kolory',
    'Chart style': 'Styl wykresu',
    'Hexadecimal colors': 'Kolory szesnastkowe',
    'Type space separated hexadecimal codes': 'Wpisz kody szesnastkowe oddzielone spacjami',
    'X axis title': 'Tytuł osi X',
    'Y axis title': 'Tytuł osi Y',
    'Chart title': 'Tytuł wykresu',
    'Line width': 'Grubość linii',
    'Download data (CSV)': 'Pobierz dane (CSV)',
    'Image format for the camera icon': 'Format obrazu dla ikony aparatu',
    'Use the camera icon above a chart to save it as an image.':
        'Użyj ikony aparatu nad wykresem, aby zapisać go jako obraz.',
    'How to start': 'Jak zacząć',
    'Supported files': 'Obsługiwane pliki',
    'Upload your spectra (*.txt or *.csv) in the left sidebar, or choose example data. '
    'Spectrometer type is detected automatically - you can upload files from different instruments at once.':
        'Wgraj widma (*.txt lub *.csv) w lewym panelu albo wybierz przykładowe dane. '
        'Typ spektrometru rozpoznawany jest automatycznie - możesz wgrać naraz pliki z różnych urządzeń.',
    'Upload raw data in *.txt format (metadata + data).': 'Wgraj surowe dane w formacie *.txt (metadane + dane).',
    'First column: Raman Shift, second column: intensity.':
        'Pierwsza kolumna: przesunięcie Ramana, druga: intensywność.',
    'Name of the file is used as the name of the spectrum.': 'Nazwa pliku jest używana jako nazwa widma.',
    'First column: Raman Shift, other columns: intensities.':
        'Pierwsza kolumna: przesunięcie Ramana, pozostałe: intensywności.',
    'Column names are shown in the legend. A file may contain several Raman Shift columns.':
        'Nazwy kolumn pojawiają się w legendzie. Plik może zawierać kilka kolumn z przesunięciem Ramana.',
    'Upload *.csv (ENLIGHTEN export) or *.txt files.': 'Wgraj pliki *.csv (eksport ENLIGHTEN) lub *.txt.',

    # chart selection
    'Tip: drag on the chart to select the peak range.': 'Wskazówka: przeciągnij po wykresie, aby zaznaczyć zakres piku.',
    'Selection on the chart sets': 'Zaznaczenie na wykresie ustawia',

    # RSD
    'Relative Standard Deviation (RSD)': 'Względne odchylenie standardowe (RSD)',
    'Choose at least two spectra': 'Wybierz co najmniej dwa widma',
    'RSD type': 'Rodzaj RSD',
    'Intensity of one peak': 'Intensywność jednego piku',
    'Ratio of two peaks': 'Stosunek dwóch pików',
    'Peak 1 range': 'Zakres piku 1',
    'Peak 2 range': 'Zakres piku 2',
    'Peak 1': 'Pik 1',
    'Peak 2': 'Pik 2',
    'Normalize chart': 'Normalizuj wykres',
    'Changes only the chart - RSD is always calculated from the original intensities':
        'Zmienia tylko wykres - RSD zawsze liczone jest z oryginalnych intensywności',
    'Peak range is too narrow': 'Zakres piku jest za wąski',
    'Results': 'Wyniki',
    'Decimal places': 'Miejsca po przecinku',
    'RAW data': 'Surowe dane',
    'Mean': 'Średnia',
    'Standard deviation': 'Odchylenie standardowe',
    'Download results (CSV)': 'Pobierz wyniki (CSV)',

    # PCA
    'Principal Component Analysis (PCA)': 'Analiza głównych składowych (PCA)',
    'PCA needs at least two spectra': 'PCA wymaga co najmniej dwóch widm',
    'Number of groups': 'Liczba grup',
    'Principal components': 'Główne składowe',
    'Group name': 'Nazwa grupy',
    '...or choose from loaded data': '...lub wybierz z wczytanych danych',
    'Upload spectra for each group, or choose them from the data loaded in the sidebar.':
        'Wgraj widma dla każdej grupy albo wybierz je z danych wczytanych w panelu bocznym.',
    'Each spectrum can belong to one group only': 'Każde widmo może należeć tylko do jednej grupy',
    'Choose at least {n} spectra': 'Wybierz co najmniej {n} widma',
    'Rescale spectra (0-1)': 'Przeskaluj widma (0-1)',
    'Group': 'Grupa',
    'Spectra used': 'Użyte widma',
    'Spectra recovered from principal components': 'Widma odtworzone z głównych składowych',
    'Details': 'Szczegóły',
    'Explained variance ratio': 'Udział wyjaśnionej wariancji',
    'Download scores (CSV)': 'Pobierz wyniki PCA (CSV)',
    'Clustering': 'Klastrowanie',
    'Find clusters': 'Znajdź klastry',
    'Groups spectra by similarity of their PCA scores, without using your group names.':
        'Grupuje widma według podobieństwa wyników PCA, bez korzystania z nazw Twoich grup.',
    'Method': 'Metoda',
    'Hierarchical (Ward)': 'Hierarchiczna (Ward)',
    'Number of clusters - automatic': 'Liczba klastrów - automatycznie',
    'Chosen by the best silhouette score.': 'Wybierana na podstawie najlepszego współczynnika silhouette.',
    'Number of clusters': 'Liczba klastrów',
    'Cluster': 'Klaster',
    'Clusters': 'Klastry',
    'Silhouette': 'Silhouette',
    'Separation of the clusters: close to 1 = well separated, around 0 = overlapping.':
        'Rozdzielenie klastrów: blisko 1 = dobrze rozdzielone, około 0 = nakładają się.',
    'Agreement with groups (ARI)': 'Zgodność z grupami (ARI)',
    'Adjusted Rand index: 1 = clusters are exactly your groups, ~0 = no relation.':
        'Skorygowany indeks Randa: 1 = klastry to dokładnie Twoje grupy, ~0 = brak związku.',
    'Number of spectra of each group in each cluster:': 'Liczba widm z każdej grupy w każdym klastrze:',
    'Loadings - which bands differ between samples': 'Ładunki - które pasma różnią próbki',
    'Large positive or negative values mark the Raman bands that the principal component '
    'is made of.': 'Duże wartości dodatnie lub ujemne wskazują pasma Ramana, z których składa się główna składowa.',
    'Loading': 'Ładunek',
    'PC 1 is dominated by bands near: {bands} cm⁻¹': 'PC 1 tworzą głównie pasma w okolicy: {bands} cm⁻¹',
    'Scree plot - variance explained by each component': 'Wykres osypiska - wariancja wyjaśniona przez składowe',
    'Component': 'Składowa',
    'Cumulative': 'Skumulowana',
    'Explained variance [%]': 'Wyjaśniona wariancja [%]',

    # calibration
    'Calibration & LOD': 'Kalibracja i LOD',
    'Calibration curve and limit of detection (LOD)': 'Krzywa kalibracyjna i granica wykrywalności (LOD)',
    'Upload spectra measured at several concentrations (replicates welcome). Concentrations are read '
    'from file names, e.g. "R6G_5x10-6M_1.txt" or "sample_1ppm.csv" - you can correct them.':
        'Wgraj widma zmierzone przy kilku stężeniach (najlepiej z powtórzeniami). Stężenia odczytywane są z nazw '
        'plików, np. „R6G_5x10-6M_1.txt” lub „probka_1ppm.csv” - możesz je poprawić.',
    'Peak range': 'Zakres piku',
    'Signal': 'Sygnał',
    'Peak height': 'Wysokość piku',
    'Peak area': 'Pole piku',
    'Concentration axis': 'Oś stężenia',
    'Linear': 'Liniowa',
    'Logarithmic': 'Logarytmiczna',
    'Unit': 'Jednostka',
    'Changing the unit converts the values (e.g. 1 µM = 0.001 mM).':
        'Zmiana jednostki przelicza wartości (np. 1 µM = 0,001 mM).',
    'Concentrations': 'Stężenia',
    'Read from file names - correct them if needed. Use 0 for blank samples.':
        'Odczytane z nazw plików - popraw w razie potrzeby. Dla ślepej próby wpisz 0.',
    'Select the peak range on the chart (drag) or with the slider.':
        'Zaznacz zakres piku na wykresie (przeciągnij) lub suwakiem.',
    'Enter concentrations for at least two different levels.': 'Wpisz stężenia dla co najmniej dwóch różnych poziomów.',
    'Standard deviation for LOD': 'Odchylenie standardowe do LOD',
    'Residuals of the fit': 'Reszty dopasowania',
    'Blank spectra (concentration 0)': 'Widma ślepej próby (stężenie 0)',
    'Blank: LOD = 3·SD(blank)/slope. Fit: LOD = 3.3·SD(residuals)/slope.':
        'Ślepa próba: LOD = 3·SD(ślepej próby)/nachylenie. Dopasowanie: LOD = 3,3·SD(reszt)/nachylenie.',
    'At least two blank (concentration 0) spectra are needed': 'Potrzebne są co najmniej dwa widma ślepej próby (stężenie 0)',
    'At least two different concentrations are needed': 'Potrzebne są co najmniej dwa różne stężenia',
    'With a logarithmic axis LOD is calculated from blank spectra - choose them as the source of the '
    'standard deviation.': 'Przy osi logarytmicznej LOD liczony jest z widm ślepej próby - wybierz je jako źródło '
                           'odchylenia standardowego.',
    'Calibration curve': 'Krzywa kalibracyjna',
    'Peak': 'Pik',
    'Peak - measured signal': 'Pik - mierzony sygnał',
    'Read from file names: {found} of {total}. Correct them if needed, use 0 for blank samples.':
        'Odczytane z nazw plików: {found} z {total}. Popraw w razie potrzeby, dla ślepej próby wpisz 0.',
    'Enter concentrations for at least two different levels in the table above (step 2).':
        'Wpisz stężenia dla co najmniej dwóch różnych poziomów w tabeli powyżej (krok 2).',
    'The signal does not increase with concentration, so LOD cannot be calculated. '
    'Check the concentrations and the peak range.':
        'Sygnał nie rośnie ze stężeniem, więc nie da się policzyć LOD. Sprawdź stężenia i zakres piku.',
    'Poor linearity (R² < 0.9) - LOD and LOQ are not reliable.':
        'Słaba liniowość (R² < 0,9) - LOD i LOQ są niewiarygodne.',
    'Slope': 'Nachylenie',
    'Mean ± SD': 'Średnia ± SD',
    'Fit': 'Dopasowanie',

    # maps
    'Uniformity map': 'Mapa jednorodności',
    'Substrate uniformity map': 'Mapa jednorodności podłoża',
    'Upload a map file (columns: X, Y, Raman Shift, Intensity - e.g. Renishaw WiRE export) or several '
    'spectra measured on a regular grid.': 'Wgraj plik mapy (kolumny: X, Y, przesunięcie Ramana, intensywność - '
                                           'np. eksport z Renishaw WiRE) albo kilka widm zmierzonych na regularnej '
                                           'siatce.',
    'A map needs at least 4 spectra.': 'Mapa wymaga co najmniej 4 widm.',
    'Measurement grid': 'Siatka pomiarowa',
    'Spectra are placed on the grid row by row, in the order of the files.':
        'Widma są układane na siatce wiersz po wierszu, w kolejności plików.',
    'Points in a row': 'Punktów w wierszu',
    'Step X [µm]': 'Krok X [µm]',
    'Step Y [µm]': 'Krok Y [µm]',
    'Snake order': 'Kolejność „wężykiem”',
    'Every second row measured in the opposite direction.': 'Co drugi wiersz mierzony w przeciwnym kierunku.',
    '{n} spectra do not fill the last row - it stays partly empty.':
        '{n} widm nie wypełnia ostatniego wiersza - zostanie częściowo pusty.',
    'Min – max': 'Min – max',
    'Mean spectrum': 'Widmo średnie',
    'Map': 'Mapa',
    'Within ±20 % of mean': 'W granicach ±20 % średniej',
    'Points': 'Punkty',
    'Show as % of mean': 'Pokaż jako % średniej',
    'Colour scale': 'Skala kolorów',
    'Distribution': 'Rozkład',
    'Download map (CSV)': 'Pobierz mapę (CSV)',

    # EF presets, uncertainty, AEF
    'Substrate EF': 'EF podłoża',
    'Analytical EF (AEF)': 'Analityczny EF (AEF)',
    'Simpler definition, often used to compare substrates: signal per concentration in SERS divided by '
    'signal per concentration in normal Raman (analyte solution measured under the same conditions).':
        'Prostsza definicja, często używana do porównywania podłoży: sygnał na jednostkę stężenia w SERS podzielony '
        'przez sygnał na jednostkę stężenia w zwykłym Ramanie (roztwór analitu mierzony w tych samych warunkach).',
    'Analyte preset': 'Analit (ustawienia)',
    'Custom': 'Własne',
    'p-MBA (4-mercaptobenzoic acid)': 'p-MBA (kwas 4-merkaptobenzoesowy)',
    '4-ATP (4-aminothiophenol)': '4-ATP (4-aminotiofenol)',
    'Rhodamine 6G': 'Rodamina 6G',
    'Crystal violet': 'Fiolet krystaliczny',
    'Objective preset (NA)': 'Obiektyw (NA)',
    'Typical values - check the numerical aperture engraved on your objective.':
        'Typowe wartości - sprawdź aperturę numeryczną wygrawerowaną na obiektywie.',
    'Only the molar mass is set for this analyte. Take density, surface coverage and penetration '
    'depth from the literature - they differ between molecules.':
        'Dla tego analitu ustawiona jest tylko masa molowa. Gęstość, pokrycie powierzchni i głębokość wnikania '
        'weź z literatury - różnią się między cząsteczkami.',
    'Uncertainty of EF': 'Niepewność EF',
    'EF depends on assumptions that are hard to measure. The range comes from 20 000 random '
    'combinations of the uncertain inputs (uniform within the ranges, normal for intensities).':
        'EF zależy od założeń, które trudno zmierzyć. Zakres pochodzi z 20 000 losowych kombinacji niepewnych '
        'danych (rozkład jednostajny w zakresach, normalny dla intensywności).',
    'Coverage from': 'Pokrycie od',
    'Coverage to': 'Pokrycie do',
    'Surface development ± [%]': 'Rozwinięcie powierzchni ± [%]',
    'Penetration depth ± [%]': 'Głębokość wnikania ± [%]',
    'SERS intensity RSD [%]': 'RSD intensywności SERS [%]',
    'Raman intensity RSD [%]': 'RSD intensywności Ramana [%]',
    'From the uploaded spectra when several SERS spectra are averaged.':
        'Z wgranych widm, gdy uśredniasz kilka widm SERS.',
    'EF range (90 %)': 'Zakres EF (90 %)',
    'Surface coverage': 'Pokrycie powierzchni',
    'Surface development': 'Rozwinięcie powierzchni',
    'Penetration depth': 'Głębokość wnikania',
    'Which input changes EF the most': 'Który parametr najbardziej zmienia EF',
    'Each bar: EF when only this input goes from the low to the high end of its range.':
        'Każdy pasek: EF, gdy tylko ten parametr zmienia się od dolnego do górnego końca zakresu.',

    # EF
    'Enhancement Factor (EF) calculator': 'Kalkulator współczynnika wzmocnienia (EF)',
    'Solution': 'Roztwór',
    'Concentration': 'Stężenie',
    'Volume of solution [µl]': 'Objętość roztworu [µl]',
    'Instrument': 'Aparatura',
    'Laser wavelength [nm]': 'Długość fali lasera [nm]',
    'Lens parameter - Numerical Aperture (NA)': 'Apertura numeryczna obiektywu (NA)',
    'SERS substrate': 'Podłoże SERS',
    'Size x [mm]': 'Wymiar x [mm]',
    'Size y [mm]': 'Wymiar y [mm]',
    'Surface area development coefficient': 'Współczynnik rozwinięcia powierzchni',
    'Rough surface ~2': 'Chropowata powierzchnia ~2',
    'The coverage of the surface by the analyte (0-1)': 'Pokrycie powierzchni analitem (0-1)',
    'e.g. ~0.1 for p-MBA 10⁻⁶ M': 'np. ~0,1 dla p-MBA 10⁻⁶ M',
    'Compound (solid, for Raman reference)': 'Związek (ciało stałe, do pomiaru Ramana)',
    'Compound density [g/cm³]': 'Gęstość związku [g/cm³]',
    'Molecular weight [g/mol]': 'Masa molowa [g/mol]',
    'Depth into which the laser penetrates the chemical compound in crystalline form [mm]':
        'Głębokość wnikania lasera w kryształ związku [mm]',
    'Intensities': 'Intensywności',
    'Type in the intensities': 'Wpisz intensywności',
    'Read them from uploaded spectra': 'Odczytaj z wgranych widm',
    'Raman Intensity': 'Intensywność Ramana',
    'SERS Intensity': 'Intensywność SERS',
    'Raman spectra': 'Widma Ramana',
    'SERS spectra': 'Widma SERS',
    'Choose {name} spectra': 'Wybierz widma {name}',
    'Raman peak range': 'Zakres piku Ramana',
    'SERS peak range': 'Zakres piku SERS',
    'Selected peak range is empty': 'Wybrany zakres piku jest pusty',
    'Choose which uploaded spectra are Raman and which are SERS. Several spectra of each type '
    '(e.g. from a map) are averaged. Choose the same band in both, e.g. ~1075 or ~1588 cm⁻¹ for p-MBA.':
        'Wybierz, które z wgranych widm to Raman, a które SERS. Kilka widm danego typu (np. z mapy) '
        'zostanie uśrednionych. Wybierz to samo pasmo w obu, np. ~1075 lub ~1588 cm⁻¹ dla p-MBA.',
    'Average of {n} spectra. Peak intensity SD: {sd} (RSD {rsd} %)':
        'Średnia z {n} widm. SD intensywności piku: {sd} (RSD {rsd} %)',
    'Show calculation step by step': 'Pokaż obliczenia krok po kroku',
    'Download parameters and results (CSV)': 'Pobierz parametry i wyniki (CSV)',
    'Load parameters from a previous calculation file': 'Wczytaj parametry z pliku poprzednich obliczeń',
    'At the bottom of this page you can download all parameters and results with '
    '"Download parameters and results (CSV)". Upload that file here to restore the calculation '
    '- e.g. the settings of your microscope - instead of typing them again.':
        'Na dole tej strony możesz pobrać wszystkie parametry i wyniki przyciskiem „Pobierz parametry i wyniki (CSV)”. '
        'Wgraj tu ten plik, aby odtworzyć obliczenia - np. ustawienia swojego mikroskopu - zamiast wpisywać je '
        'od nowa.',
    'CSV file downloaded earlier from this page': 'Plik CSV pobrany wcześniej z tej strony',
    'This is not a parameters file downloaded from this page.': 'To nie jest plik z parametrami pobrany z tej strony.',
    'Loaded {n} parameters.': 'Wczytano parametrów: {n}.',
    'Skipped (out of range): {keys}': 'Pominięto (poza zakresem): {keys}',
    'Parameter': 'Parametr',
    'Value': 'Wartość',
    'Number of molecules in the solution': 'Liczba cząsteczek w roztworze',
    'Laser spot diameter': 'Średnica plamki lasera',
    'Laser spot area': 'Pole plamki lasera',
    'Molecules on the irradiated SERS surface': 'Cząsteczki na oświetlonej powierzchni SERS',
    'Irradiated volume of the solid compound': 'Oświetlona objętość kryształu',
    'Molecules irradiated in the Raman measurement': 'Cząsteczki oświetlone w pomiarze Ramana',
    'Method: P. Piecyk, A. Kowalska, T. Szymborski, IChF PAN 2020.':
        'Metoda: P. Piecyk, A. Kowalska, T. Szymborski, IChF PAN 2020.',
    'Upload Raman and SERS spectra in the sidebar': 'Wgraj widma Ramana i SERS w panelu bocznym',
    "Subtract substrate background":
        "Odejmij tło podłoża",
    "Removes the bands of the bare substrate. Measure the substrate without the analyte (blank) with the same settings and use it as the background.":
        "Usuwa pasma samego podłoża. Zmierz podłoże bez analitu (ślepą próbę) z tymi samymi ustawieniami i użyj go jako tła.",
    "Background":
        "Tło",
    "One of the loaded spectra":
        "Jedno z wgranych widm",
    "Separate file":
        "Osobny plik",
    "Background spectra (averaged)":
        "Widma tła (uśredniane)",
    "Choose the spectrum of the bare substrate.":
        "Wybierz widmo samego podłoża.",
    "All spectra are chosen as background - nothing left to correct.":
        "Wszystkie widma wybrano jako tło – nie ma czego korygować.",
    "Background file":
        "Plik z tłem",
    "Upload the spectrum of the bare substrate (blank).":
        "Wgraj widmo samego podłoża (ślepej próby).",
    "Background scale":
        "Skala tła",
    "Automatic (fitted for every spectrum)":
        "Automatyczna (dopasowana do każdego widma)",
    "Fixed factor":
        "Stały współczynnik",
    "Automatic: the background is fitted to every spectrum together with a smooth polynomial, analyte peaks are left out of the fit. Fixed: the same factor for all spectra, e.g. 1 when the background was measured with the same settings.":
        "Automatyczna: tło jest dopasowywane do każdego widma razem z gładkim wielomianem, piki analitu są pomijane w dopasowaniu. Stała: ten sam współczynnik dla wszystkich widm, np. 1, gdy tło zmierzono z tymi samymi ustawieniami.",
    "Factor":
        "Współczynnik",
    "Background scale factor: {f}":
        "Współczynnik skali tła: {f}",
    "The background does not cover the Raman Shift range of the spectra.":
        "Tło nie obejmuje zakresu przesunięcia Ramana widm.",
    "Substrate background":
        "Tło podłoża",
    "Background subtracted":
        "Po odjęciu tła",
    "on":
        "włączone",
    "off":
        "wyłączone",
    "not set":
        "nie wybrano tła",
    "Background spectra are not shown as samples.":
        "Widma tła nie są pokazywane jako próbki.",
    "SNIP baseline: half window [cm⁻¹]":
        "Linia bazowa SNIP: półokno [cm⁻¹]",
    "About twice the width (FWHM) of the peaks, e.g. 40 cm⁻¹ for p-MBA. Too small cuts into the peaks, too large leaves fluorescence under them.":
        "Około dwukrotność szerokości pików (FWHM), np. 40 cm⁻¹ dla p-MBA. Za małe ścina piki, za duże zostawia pod nimi fluorescencję.",
    'Baseline under the peak':
        'Linia bazowa pod pikiem',
    'Straight line under the peak':
        'Prosta pod pikiem',
    'None (absolute height)':
        'Brak (wysokość bezwzględna)',
    'What counts as zero under the peak. SNIP: baseline of the whole spectrum. Straight line: fitted under the peak range only. None: absolute height, fluorescence and background included - e.g. a peak 10 000 high on a 30 000 background counts as 40 000.':
        'Co jest zerem pod pikiem. SNIP: linia bazowa całego widma. Prosta: dopasowana tylko w zakresie piku. Brak: wysokość bezwzględna, razem z fluorescencją i tłem – np. pik o wysokości 10 000 na tle 30 000 liczy się jako 40 000.',
    'Detector saturated in: {names}. The top of the strongest peak is cut off, so its height is too low (e.g. EF lower by ~10 %). Measure again with lower laser power or a shorter time.':
        'Detektor nasycony w: {names}. Wierzchołek najsilniejszego piku jest ścięty, więc jego wysokość jest za niska (np. EF niższy o ~10 %). Zmierz ponownie z mniejszą mocą lasera albo krótszym czasem.',
    '95 % CI':
        'przedział 95 %',
    'RSD 95 % CI from [%]':
        'RSD, przedział 95 % od [%]',
    'RSD 95 % CI to [%]':
        'RSD, przedział 95 % do [%]',
    '95 % CI: the range in which the true RSD of the substrate lies. It narrows with more spectra - a measured RSD of 10 % means 6–29 % from 5 spectra and 8–15 % from 20.':
        'Przedział 95 %: zakres, w którym leży prawdziwe RSD podłoża. Zwęża się z liczbą widm – zmierzone RSD 10 % oznacza 6–29 % przy 5 widmach i 8–15 % przy 20.',
    "Moran's I = {i} (p = {p}): neighbouring points resemble each other - the differences form patches or a gradient, e.g. uneven deposition. Look at the map for weaker areas.":
        'I Morana = {i} (p = {p}): sąsiednie punkty są do siebie podobne – różnice układają się w plamy albo gradient, np. nierówne nanoszenie. Poszukaj na mapie słabszych obszarów.',
    "Moran's I = {i} (p = {p}): neighbouring points differ more than by chance - check the order of the points (snake order) and the stage.":
        'I Morana = {i} (p = {p}): sąsiednie punkty różnią się bardziej niż przypadkowo – sprawdź kolejność punktów (wężykiem) i stolik.',
    "Moran's I = {i} (p = {p}): the differences between points look random - no gradient or patches.":
        'I Morana = {i} (p = {p}): różnice między punktami wyglądają na losowe – bez gradientu i plam.',
    'Same RSD, different substrate: scattered weak points (random) are noise, a weaker edge or patch (clustered) points to the production process. p = how often a random shuffle of the same values over the map looks at least as clustered.':
        'To samo RSD, inne podłoże: rozrzucone słabsze punkty (losowo) to szum, słabszy brzeg albo plama (skupienia) wskazują na proces produkcji. p = jak często losowe przetasowanie tych samych wartości na mapie wygląda na co najmniej tak samo skupione.',
}
