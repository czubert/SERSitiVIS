"""
Anonymous visit statistics in Firestore - numbers only: no cookies, no IP address, no file contents, nothing that
identifies a person. One document per day (UTC) in the 'visits' collection, e.g. visits/2026-11-14:
    {'visits': 41, 'pages': {'rsd': 12, 'calibration': 7}, 'languages': {'pl': 20, 'en': 30},
     'formats': {'BWTEK': 3, 'WDF': 1}, 'examples': {'Renishaw': 5}, 'reports': {'rsd': 2}}
visits = new sessions, pages and languages = page views, formats = uploaded files, examples = example data chosen,
reports = PDF reports created.

Turned on by the Streamlit secret 'firebase_credentials' (service account JSON, as in the old app). Without it
(local runs, tests) nothing is sent. Writes run in the background and a failed write never stops the app.
"""
import json
import logging
import re
import threading
from datetime import datetime, timezone

import streamlit as st

COLLECTION = 'visits'
SECRET = 'firebase_credentials'
SEEN = '_visits_seen'  # what was already counted in this session

log = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def _client():
    try:
        info = st.secrets[SECRET]
    except Exception:  # no secrets file or no key - statistics off
        return None
    try:
        from google.cloud import firestore

        info = json.loads(info) if isinstance(info, str) else dict(info)
        return firestore.Client.from_service_account_info(info)
    except Exception:
        log.exception('Visit statistics are off')
        return None


def field(name):
    """Firestore field name: 'WITec Alpha300 R+' -> 'WITec_Alpha300_R_'"""
    return re.sub(r'\W', '_', str(name)) or '_'


def page_counts(seen, page, language):
    """
    What to count for this run of the app: a visit once per session, a page view when the page changes
    :param seen: Dict kept in the session (changed here)
    :return: Dict of increments, e.g. {'visits': 1, 'pages': {'rsd': 1}, 'languages': {'pl': 1}}
    """
    counts = {}
    if not seen.get('visit'):
        seen['visit'] = True
        counts['visits'] = 1
    if seen.get('page') != page:
        seen['page'] = page
        counts['pages'] = {field(page): 1}
        counts['languages'] = {field(language): 1}
    return counts


def file_counts(seen, loaded, example=None):
    """
    Uploaded files by format (each file once per session), or the example data set chosen
    :param loaded: list of readers.LoadedFile
    """
    if example:
        key = ('example', example)
        if key in seen.setdefault('files', set()):
            return {}
        seen['files'].add(key)
        return {'examples': {field(example): 1}}
    counts = {}
    for f in loaded:
        key = (f.name, f.data.shape)
        if key not in seen.setdefault('files', set()):
            seen['files'].add(key)
            counts[field(f.format)] = counts.get(field(f.format), 0) + 1
    return {'formats': counts} if counts else {}


def _send(counts):
    """Adds the counts to today's document, in the background"""
    client = _client()
    if not counts or client is None:
        return
    from google.cloud import firestore

    update = {name: ({key: firestore.Increment(n) for key, n in value.items()} if isinstance(value, dict)
                     else firestore.Increment(value))
              for name, value in counts.items()}
    document = client.collection(COLLECTION).document(datetime.now(timezone.utc).strftime('%Y-%m-%d'))

    def write():
        try:
            document.set(update, merge=True)
        except Exception:
            log.exception('Visit not counted')

    threading.Thread(target=write, daemon=True).start()


def track_page(page, language):
    _send(page_counts(st.session_state.setdefault(SEEN, {}), page, language))


def track_files(loaded, example=None):
    _send(file_counts(st.session_state.setdefault(SEEN, {}), loaded, example))


def track_report(page):
    _send({'reports': {field(page): 1}})
