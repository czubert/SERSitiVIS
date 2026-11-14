"""
Substrate background subtraction - one panel, the same on every page that measures spectra.
The blank substrate belongs to the data, not to a page: the setting is kept for the whole session and the
background spectra are hidden from the samples everywhere. The panel header says whether it is on.
"""
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from core import processing
from vis_helpers import workspace
from vis_helpers.i18n import t, choice

SOURCES = {'loaded': 'One of the loaded spectra', 'file': 'Separate file'}
SCALES = {'auto': 'Automatic (fitted for every spectrum)', 'manual': 'Fixed factor'}
NAME_HINTS = ('blank', 'background', 'substrate', 'tlo', 'tło', 'bg', 'podloze', 'podłoże')

ON, SOURCE, SPECTRA, FILE, SCALE, FACTOR = 'bg_subtract', 'bg_source', 'bg_spectra', 'bg_file', 'bg_scale', 'bg_factor'
DEFAULTS = {ON: False, SOURCE: 'loaded', SPECTRA: [], FACTOR: 1.0}


@dataclass
class Settings:
    spectra: pd.DataFrame  # background spectra, averaged when subtracted
    names: list
    scale: object  # 'auto' or a number
    note: object  # placeholder in the panel for the result of the subtraction


@dataclass
class Subtraction:
    settings: Settings
    factors: dict  # {spectrum: scale factor}
    background: pd.Series  # on the Raman Shift grid of the corrected spectra

    def scaled(self, name):
        return self.factors[name] * self.background


def _value(key):
    """
    Setting kept for the whole session. Streamlit forgets the state of widgets that are not shown, e.g. after
    a page change, so every widget value is copied to a plain session_state key (like i18n.choice does).
    """
    return st.session_state.get(f'_{key}', DEFAULTS.get(key))


def _kept(key):
    """Widget arguments: start from the kept value (also on a page that has not shown the widget yet), keep changes"""
    st.session_state[key] = _value(key)
    return dict(key=key, on_change=lambda: st.session_state.update({f'_{key}': st.session_state[key]}))


def _chosen(df):
    """Loaded spectra chosen as the background (empty if all spectra are chosen - nothing would be left)"""
    names = [n for n in _value(SPECTRA) if n in df.columns]
    return names if len(names) < df.shape[1] else []


def _ready(df):
    if not _value(ON):
        return False
    return bool(_chosen(df)) if _value(SOURCE) == 'loaded' else bool(st.session_state.get(f'_stored_{FILE}'))


def samples(df):
    """Spectra without the background spectra (they are the blank substrate, not samples)"""
    if _value(ON) and _value(SOURCE) == 'loaded':
        return df.drop(columns=_chosen(df))
    return df


def panel(df):
    """
    Expander with the background settings. Its header shows whether the background is subtracted.
    :param df: all loaded spectra (the background can be one of them)
    :return: Settings or None
    """
    state = t('on') if _ready(df) else t('not set') if _value(ON) else t('off')
    with st.expander(f'{t("Substrate background")}: {state}', key='bg_panel', icon=':material/layers_clear:'):
        return _settings(df)


def panel_if_hidden(all_df, df):
    """
    For pages that stop when there are too few spectra: if background spectra are hidden, the panel is shown,
    so it is clear where the spectra went and the setting can be changed right there
    """
    if df.shape[1] < all_df.shape[1]:
        panel(all_df)


def _settings(df):
    if not st.checkbox(t('Subtract substrate background'), **_kept(ON),
                       help=t('Removes the bands of the bare substrate. Measure the substrate without the analyte '
                              '(blank) with the same settings and use it as the background.')):
        return None

    source = choice('radio', t('Background'), list(SOURCES), key=SOURCE, format_func=lambda s: t(SOURCES[s]))
    if source == 'loaded':
        if f'_{SPECTRA}' not in st.session_state:  # first time: guess from file names (blank, background, tło...)
            st.session_state[f'_{SPECTRA}'] = [n for n in df.columns
                                               if any(h in str(n).lower() for h in NAME_HINTS)][:1]
        st.session_state[f'_{SPECTRA}'] = [n for n in _value(SPECTRA) if n in df.columns]  # other data loaded
        names = st.multiselect(t('Background spectra (averaged)'), list(df.columns), **_kept(SPECTRA))
        if not names:
            st.info(t('Choose the spectrum of the bare substrate.'))
            return None
        if len(names) == df.shape[1]:
            st.warning(t('All spectra are chosen as background - nothing left to correct.'))
            return None
        st.caption(t('Background spectra are not shown as samples.'))
        spectra = df[names]
    else:
        _, spectra = workspace.stored_uploader(t('Background file'), key=FILE)
        if spectra is None:
            st.info(t('Upload the spectrum of the bare substrate (blank).'))
            return None
        names = list(spectra.columns)

    scale = choice('radio', t('Background scale'), list(SCALES), key=SCALE, format_func=lambda s: t(SCALES[s]),
                   help=t('Automatic: the background is fitted to every spectrum together with a smooth '
                          'polynomial, analyte peaks are left out of the fit. Fixed: the same factor for all spectra, '
                          'e.g. 1 when the background was measured with the same settings.'))
    if scale == 'manual':
        scale = st.number_input(t('Factor'), min_value=0.0, step=0.1, format='%.3f', **_kept(FACTOR))
    return Settings(spectra, names, scale, st.empty())


@st.cache_data(show_spinner=False, max_entries=8)
def _subtract(df, spectra, scale):
    return processing.subtract_background(df, spectra, scale)


def subtract(df, settings, despike=None):
    """
    :param settings: Settings from panel() or None
    :param despike: spike threshold used for the samples - the background gets the same treatment
    :return: (spectra after subtraction, Subtraction or None)
    """
    if settings is None:
        return df, None
    spectra = processing.remove_spikes(settings.spectra, despike)[0] if despike else settings.spectra
    try:
        corrected, factors, background = _subtract(df, spectra, settings.scale)
    except ValueError:
        settings.note.warning(t('The background does not cover the Raman Shift range of the spectra.'))
        return df, None
    values = list(factors.values())
    text = f'{values[0]:.3g}' if len(set(values)) == 1 else f'{min(values):.3g} – {max(values):.3g}'
    settings.note.caption(t('Background scale factor: {f}').format(f=text))
    return corrected, Subtraction(settings, factors, background)


def describe(subtraction):
    """For reports: background spectra and scale, or a dash"""
    if subtraction is None:
        return '—'
    settings = subtraction.settings
    scale = t(SCALES['auto']) if settings.scale == 'auto' else f'{t("Factor")} {settings.scale:.3g}'
    return f'{", ".join(map(str, settings.names))} ({scale})'
