"""Local acquisition preview and opt-in bounded live research. No outreach or lead writes."""
from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timezone
import os
import logging
import sqlite3
import threading
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .models import Candidate, DiscoveryRequest, Evidence
from .discovery import shortlist
from .live_discovery import discover_live, DiscoveryFailure

logger = logging.getLogger(__name__)

router = APIRouter()
_usage_lock = threading.Lock()
MAX_RUNS_PER_UTC_DAY = 5
_STATIC = Path(__file__).with_name('ui')

class PreviewInput(BaseModel):
    seller_website: str = Field(max_length=500)
    offering: str = Field(min_length=1, max_length=1500)
    ideal_customer_profile: str = Field(min_length=1, max_length=1500)
    max_results: int = Field(default=10, ge=1, le=10)

# Fictional examples only; domains are reserved for documentation.
_FICTIONAL = (
    Candidate('Northstar Field Systems (fictional)', 'northstar.example.org',
              'Example only: could match a field-service automation ICP.',
              (Evidence('DEMO-1', 'https://example.org/northstar', 'Illustrative synthetic research note, not a live citation.'),),
              ('Company existence', 'Budget', 'Actual technology stack')),
    Candidate('Harborline Logistics (fictional)', 'harborline.example.org',
              'Example only: could match a logistics operations ICP.',
              (Evidence('DEMO-2', 'https://example.org/harborline', 'Illustrative synthetic research note, not a live citation.'),),
              ('Company existence', 'Purchasing intent')),
)

@router.get('/acquisition')
def acquisition_screen():
    return FileResponse(_STATIC / 'index.html')

@router.get('/acquisition/ui.css')
def acquisition_styles():
    return FileResponse(_STATIC / 'ui.css', media_type='text/css')

@router.get('/acquisition/ui.js')
def acquisition_script():
    return FileResponse(_STATIC / 'ui.js', media_type='application/javascript')

@router.post('/api/acquisition/preview')
def acquisition_preview(payload: PreviewInput):
    try:
        req = DiscoveryRequest(**payload.model_dump())
        result = shortlist(req, _FICTIONAL)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return {
        'mode': 'fictional_preview_only',
        'disclaimer': 'Fictional demonstration. No company discovery, API request, database write, or outreach was performed.',
        'candidates': [asdict(x) for x in result.candidates],
        'considered': result.considered,
        'excluded_duplicates': result.excluded_duplicates,
    }


class LiveInput(PreviewInput):
    consent_to_api: bool = False


def _reserve_live_attempt():
    """Persistent local quota. Failed/interrupted calls count. Independent of lead DB."""
    default = Path.home() / '.signaldesk' / 'acquisition_usage.sqlite3'
    path = Path(os.environ.get('SIGNALDESK_ACQUISITION_USAGE_DB', str(default)))
    today = datetime.now(timezone.utc).date().isoformat()
    with _usage_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path, timeout=10) as db:
            db.execute('CREATE TABLE IF NOT EXISTS acquisition_usage (day TEXT PRIMARY KEY, attempts INTEGER NOT NULL)')
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT attempts FROM acquisition_usage WHERE day = ?', (today,)).fetchone()
            n = row[0] if row else 0
            if n >= MAX_RUNS_PER_UTC_DAY:
                raise HTTPException(429, 'Acquisition research limit reached: five attempts per UTC day, including failures.')
            db.execute('INSERT INTO acquisition_usage(day, attempts) VALUES(?, 1) ON CONFLICT(day) DO UPDATE SET attempts=attempts+1', (today,))
            db.commit()


@router.post('/api/acquisition/live')
def acquisition_live(payload: LiveInput):
    if not payload.consent_to_api:
        raise HTTPException(422, 'Confirm that the entered seller/ICP context will be sent to OpenAI and may incur charges.')
    try:
        req = DiscoveryRequest(payload.seller_website, payload.offering, payload.ideal_customer_profile, payload.max_results)
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    if not os.getenv('OPENAI_API_KEY'):
        raise HTTPException(503, 'OPENAI_API_KEY is not configured locally. Preview mode remains available.')
    _reserve_live_attempt()
    try:
        from openai import OpenAI
        client = OpenAI(max_retries=0, timeout=60)
        report = discover_live(req, client=client)
    except DiscoveryFailure as exc:
        logger.warning('Acquisition research rejected: category=%s provider_type=%s', exc.code, exc.provider_type or 'none')
        raise HTTPException(502, 'Research returned insufficient or invalid citation evidence; no candidates accepted.') from None
    except Exception as exc:
        logger.error('Acquisition unexpected error: category=unexpected_error type=%s', type(exc).__name__)
        raise HTTPException(502, 'Live research failed; no candidates accepted.') from None
    return {
        'mode': 'live_research_unverified',
        'disclaimer': 'Public web citations are traceable, not proof of claim accuracy. Verify every company, cited claim, and business fit before taking action. No lead was created, approved, or contacted.',
        'candidates': [asdict(c) for c in report.shortlist.candidates],
        'considered': report.shortlist.considered,
        'excluded_duplicates': report.shortlist.excluded_duplicates,
        'research_calls': report.research_calls,
    }
