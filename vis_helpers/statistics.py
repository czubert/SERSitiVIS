"""
Visit statistics for the SERSitive team: a hidden page (/statistics, not in the menu) behind a password.
Password: Streamlit secret 'statistics_password'. Data: daily documents written by vis_helpers.visits.
"""
import hmac
import time
from datetime import date, timedelta

import plotly.express as px
import streamlit as st

from core import readers
from vis_helpers import visits, vis_utils
from vis_helpers.i18n import t, choice

PASSWORD_SECRET = 'statistics_password'
UNLOCKED = '_statistics_unlocked'
PERIODS = {7: 'Last 7 days', 30: 'Last 30 days', 90: 'Last 90 days', 365: 'Last 12 months'}
GROUP_TITLES = {'pages': 'Pages', 'languages': 'Languages', 'formats': 'Formats of uploaded files',
                'examples': 'Example data', 'reports': 'PDF reports'}
PAGE_TITLES = {'start': 'Start', 'visualisation': 'Visualisation', 'rsd': 'RSD', 'calibration': 'Calibration & LOD',
               'maps': 'Uniformity map', 'enhancement_factor': 'Enhancement Factor', 'pca': 'PCA'}
LANGUAGES = {'en': 'English', 'pl': 'Polski', 'de': 'Deutsch', 'uk': 'Українська'}


def _password():
    try:
        return st.secrets[PASSWORD_SECRET]
    except Exception:  # no secrets file or no key
        return None


def unlocked():
    """Password form; True once the right password was typed in this session"""
    password = _password()
    if not password:
        st.info(t('Statistics are off: set the Streamlit secret "statistics_password".'))
        return False
    if st.session_state.get(UNLOCKED):
        return True
    with st.form('statistics_login'):
        typed = st.text_input(t('Password'), type='password', key='statistics_password')
        if st.form_submit_button(t('Show statistics'), icon=':material/lock_open:'):
            if hmac.compare_digest(typed.encode(), str(password).encode()):
                st.session_state[UNLOCKED] = True
                st.rerun()
            time.sleep(1)  # slows down guessing
            st.error(t('Wrong password'))
    return False


def label(group, key):
    """Readable name of a counted item: 'enhancement_factor' -> 'Enhancement Factor', 'pl' -> 'Polski'"""
    if group == 'pages':
        return t(PAGE_TITLES.get(key, key))
    if group == 'languages':
        return LANGUAGES.get(key, key)
    if group == 'formats':
        return t(readers.FORMATS[key]) if key in readers.FORMATS else key
    if group == 'reports':
        return t(PAGE_TITLES.get(key, {'map': 'Uniformity map'}.get(key, key)))
    return key.replace('_', ' ')


def ranking_chart(totals, group):
    """Horizontal bars, largest on top, value at the end of each bar"""
    names = [label(group, key) for key in totals.index]
    fig = px.bar(x=totals.to_numpy()[::-1], y=names[::-1], orientation='h', text=totals.to_numpy()[::-1],
                 color_discrete_sequence=[vis_utils.sersitive_palette()[1]])
    fig.update_traces(textposition='outside', cliponaxis=False, hovertemplate='%{y}: %{x}<extra></extra>')
    fig.update_layout(height=90 + 32 * len(totals), margin=dict(l=10, r=40, t=10, b=10), bargap=0.35)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(title=None)
    settings = vis_utils.default_chart_settings()
    settings['titles'] = {'x': '', 'y': '', 'title': ''}
    vis_utils.show_chart(fig, settings, lines=False)


def main():
    st.header(t('Visit statistics'))
    if not unlocked():
        return
    days = visits.load_days()
    if days is None:
        st.warning(t('Not connected to the statistics database - set the Streamlit secret "firebase_credentials".'))
        return

    period = choice('radio', t('Period'), list(PERIODS), key='statistics_period', horizontal=True,
                    format_func=lambda p: t(PERIODS[p]), label_visibility='collapsed')
    end = date.today()
    start = end - timedelta(days=period - 1)
    table = visits.daily_table(days, start, end)
    previous = visits.daily_table(days, start - timedelta(days=period), start - timedelta(days=1))

    def total(data, group=None):
        return int(data['visits'].sum()) if group is None else int(visits.group_totals(data, group).sum())

    tiles = [(t('Visits'), None), (t('Page views'), 'pages'), (t('Files uploaded'), 'formats'),
             (t('PDF reports'), 'reports')]
    for column, (name, group) in zip(st.columns(4), tiles):
        now, before = total(table, group), total(previous, group)
        column.metric(name, f'{now:,}'.replace(',', ' '), delta=now - before, border=True,
                      help=t('Change against the previous period of the same length.'))

    per_week = period > 90  # a year of daily bars is unreadable
    series = table['visits'].resample('W-MON', label='left', closed='left').sum() if per_week else table['visits']
    fig = px.bar(x=series.index, y=series.to_numpy(), color_discrete_sequence=[vis_utils.sersitive_palette()[0]])
    fig.update_traces(hovertemplate='%{x|%d.%m.%Y}: %{y}<extra></extra>')
    fig.update_layout(height=320, bargap=0.25)
    settings = vis_utils.default_chart_settings()
    settings['titles'] = {'x': '', 'y': t('Visits'), 'title': t('Visits per week') if per_week else t('Visits per day')}
    vis_utils.show_chart(fig, settings, lines=False)

    columns = st.columns(2)
    for i, group in enumerate(visits.GROUPS):
        totals = visits.group_totals(table, group)
        with columns[i % 2]:
            st.subheader(t(GROUP_TITLES[group]))
            if totals.empty:
                st.caption(t('Nothing in this period.'))
            else:
                ranking_chart(totals, group)

    vis_utils.download_csv(table.reset_index(), 'sersitivis_visits.csv', t('Download data (CSV)'), 'statistics_csv',
                           index=False)
    st.caption(t('Numbers only, refreshed every 5 minutes: no cookies, IP addresses or file contents. A visit is a new '
                 'session - one person opening the app twice in one day counts twice.'))
    if st.button(t('Lock'), icon=':material/lock:'):
        st.session_state.pop(UNLOCKED)
        st.rerun()
