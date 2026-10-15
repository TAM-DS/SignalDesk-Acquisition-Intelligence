"""Single-user local demo. Approval is enforced by API state, not by a prompt."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import threading
from uuid import uuid4
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Integer, JSON, String, Text, create_engine, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .fixtures import LEADS, OFFER
from .live import NewLead, configuration, research_and_draft, LiveFailure

load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=False)
live_reservation_lock = threading.Lock()


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(30))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    approved_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    suppressed: Mapped[bool] = mapped_column(Boolean, default=False)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(50))
    detail: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[str] = mapped_column(String(50))


class Action(BaseModel):
    revision: int = Field(ge=1)
    reason: str = Field(default="", max_length=1000)


class ResearchRun(Base):
    __tablename__ = 'research_runs'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(80), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[str] = mapped_column(String(50))
    detail: Mapped[dict] = mapped_column(JSON)


class Edit(Action):
    recipient: str = Field(min_length=3, max_length=254)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


def fingerprint(data):
    payload = {k: data[k] for k in ("recipient", "subject", "body", "sources", "claims")}
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def review_flags(data):
    text = data["subject"] + " " + data["body"]
    checks = [(r"\b(wife|husband|spouse|children|daughter|son)\b", "Personal-life reference"),
              (r"\bguarantee\w*\b", "Unapproved guarantee"),
              (r"\bdear\s+x\b|\[insert|\{\{", "Unresolved placeholder"),
              (r"\b(i|we) (love|loved|enjoyed) (watching|your)\b", "Potential invented familiarity")]
    return [label for pattern, label in checks if re.search(pattern, text, re.I)]


def present(row):
    return {**row.data, "id": row.id, "state": row.state, "revision": row.revision,
            "suppressed": row.suppressed, "flags": review_flags(row.data),
            "approval_matches": bool(row.approved_hash and row.approved_hash == fingerprint(row.data))}


def create_app(database_url=None):
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./signaldesk.db")
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})

    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            # Single-worker local app: unfinished runs cannot resume automatically.
            for run in db.scalars(select(ResearchRun).where(ResearchRun.status == 'running')):
                run.status = 'interrupted'
                run.detail = {'error': 'Server restarted. Run was interrupted; provider usage may be unknown.'}
                row = db.get(Lead, run.lead_id)
                if row and row.state == 'researching' and row.revision == run.revision:
                    row.state = 'research_needed'
                    row.data = {**row.data, 'hold': 'Research interrupted by server restart. Retry manually.'}
                    row.revision += 1
            db.commit()
            if db.scalar(select(Lead.id).limit(1)) is None:
                for item in LEADS:
                    state = "blocked" if item["suppressed"] else "research_needed" if item["hold"] else "needs_review"
                    db.add(Lead(id=item["id"], data=item, state=state, revision=1, suppressed=item["suppressed"]))
                db.commit()
        yield
        engine.dispose()

    app = FastAPI(title="SignalDesk local demo", lifespan=lifespan)
    app.state.engine = engine
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            if parsed.netloc != request.headers.get("host") or parsed.scheme not in ("http", "https"):
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Cross-origin changes are not allowed."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        return response

    @app.get("/api/workspace")
    def workspace():
        return {"name": "SignalDesk", "mode": "mixed_local", "offer": OFFER,
                "delivery": "simulated_only", "live": configuration(),
                "notice": "Fixture leads remain synthetic. New live leads use OpenAI only when you explicitly run research. No email is sent."}

    @app.post('/api/leads')
    def add_lead(payload: NewLead):
        if not payload.consent_to_api:
            raise HTTPException(422, 'Acknowledge that live research sends the entered context to OpenAI.')
        id = 'live-' + uuid4().hex[:16]
        data = {**payload.model_dump(exclude={'consent_to_api'}), 'id': id, 'mode': 'live',
                'sector': 'Live company', 'employee_count': None, 'recipient': 'review@example.com',
                'sources': [], 'claims': [], 'rationale': 'Awaiting sourced research against your criteria.',
                'subject': '', 'body': '', 'hold': 'Run live research to gather evidence.', 'suppressed': False}
        with Session(engine) as db:
            row = Lead(id=id, data=data, state='research_needed', revision=1, suppressed=False)
            db.add(row)
            db.add(Event(lead_id=id, action='created', detail='Live lead added. No API call made yet; delivery remains simulated.', timestamp=datetime.now(timezone.utc).isoformat()))
            db.commit()
            return present(row)

    @app.get('/api/leads/{lead_id}/runs')
    def runs(lead_id: str):
        with Session(engine) as db:
            return [{'id': r.id, 'status': r.status, 'created_at': r.created_at, **r.detail}
                    for r in db.scalars(select(ResearchRun).where(ResearchRun.lead_id == lead_id).order_by(ResearchRun.created_at.desc()))]

    @app.post('/api/leads/{lead_id}/generate')
    def generate(lead_id: str, payload: Action):
        if not configuration()['configured']:
            raise HTTPException(503, 'Configure your OpenAI API key locally before running live research.')
        today = datetime.now(timezone.utc).date().isoformat()
        run_id = uuid4().hex
        with live_reservation_lock, Session(engine) as db:
            row = db.get(Lead, lead_id)
            if not row:
                raise HTTPException(404, 'Lead not found.')
            if row.data.get('mode') != 'live':
                raise HTTPException(409, 'Fictional fixture leads cannot be researched on the live web. Add a live lead.')
            if row.suppressed or row.state in ('blocked', 'delivered', 'researching'):
                raise HTTPException(409, 'This lead is suppressed, already delivered, or research is running.')
            if row.revision != payload.revision:
                raise HTTPException(409, 'Lead changed. Refresh before running research.')
            recent = list(db.scalars(select(ResearchRun).where(ResearchRun.created_at >= today)))
            if len(recent) >= 20 or sum(r.lead_id == lead_id for r in recent) >= 3:
                raise HTTPException(429, 'Local daily run cap reached (20 total / 3 per lead, UTC).')
            snapshot = dict(row.data)
            reserved_revision = row.revision + 1
            changed = db.execute(update(Lead).where(Lead.id == lead_id, Lead.revision == payload.revision).values(
                revision=reserved_revision, state='researching', approved_hash=None,
                data={**snapshot, 'hold': 'Research in progress. Prior approval revoked.', 'subject': '', 'body': '', 'claims': []}))
            if changed.rowcount != 1:
                raise HTTPException(409, 'Concurrent change. Refresh before retrying.')
            db.add(ResearchRun(id=run_id, lead_id=lead_id, revision=reserved_revision, status='running', created_at=datetime.now(timezone.utc).isoformat(), detail={}))
            db.add(Event(lead_id=lead_id, action='live_started', detail='Bounded OpenAI research started; approval revoked. Up to two response calls; no email delivery.', timestamp=datetime.now(timezone.utc).isoformat()))
            db.commit()
        error = None
        try:
            output = research_and_draft(snapshot, payload.reason.strip() or snapshot.get('research_question', ''))
        except Exception as exc:
            error = str(exc) if isinstance(exc, LiveFailure) else 'Live research could not start. Check API configuration and installed dependencies.'
            output = {'usage': getattr(exc, 'usage', []), 'hold': error, 'subject': '', 'body': '', 'claims': []}
        with Session(engine) as db:
            row = db.get(Lead, lead_id)
            run = db.get(ResearchRun, run_id)
            # Check revision again after external work; an intervening suppression always wins.
            values = {**snapshot, **output}
            result = db.execute(update(Lead).where(Lead.id == lead_id, Lead.revision == reserved_revision,
                Lead.suppressed == False, Lead.state == 'researching').values(
                data=values, state='research_needed' if output.get('hold') else 'needs_review',
                revision=reserved_revision + 1, approved_hash=None))
            run.detail = {'usage': output.get('usage', []), 'model': configuration()['model'],
                          'error': error, 'billing_note': 'Token counts are recorded when returned. No dollar-cost estimate; failed requests may still incur usage.'}
            if result.rowcount != 1:
                run.status = 'discarded'
                db.add(Event(lead_id=lead_id, action='live_discarded', detail='Lead changed during research. Results were not applied; later decisions preserved.', timestamp=datetime.now(timezone.utc).isoformat()))
                db.commit()
                raise HTTPException(409, 'Lead changed during research. Results discarded; your later decision was preserved.')
            run.status = 'failed' if error else 'held' if output.get('hold') else 'completed'
            db.add(Event(lead_id=lead_id, action='live_failed' if error else 'live_completed',
                detail=error or ('Research completed; evidence hold remains.' if output.get('hold') else 'AI draft returned for human review. Citations are unverified until reviewed.'),
                timestamp=datetime.now(timezone.utc).isoformat()))
            db.commit()
            db.expire_all()
            if error:
                raise HTTPException(502, error)
            return present(db.get(Lead, lead_id))

    @app.get("/api/leads")
    def leads():
        with Session(engine) as db:
            return [present(x) for x in db.scalars(select(Lead).order_by(Lead.id))]

    @app.get("/api/leads/{lead_id}/events")
    def events(lead_id: str):
        with Session(engine) as db:
            return [{"id": x.id, "action": x.action, "detail": x.detail, "timestamp": x.timestamp}
                    for x in db.scalars(select(Event).where(Event.lead_id == lead_id).order_by(Event.id.desc()))]

    def change(lead_id, command, payload):
        with Session(engine) as db:
            row = db.get(Lead, lead_id)
            if not row:
                raise HTTPException(404, "Lead not found.")
            # A delivered item cannot be edited or delivered again. Suppression remains possible.
            if command == "simulate" and row.state == "delivered":
                return {**present(row), "idempotent": True}
            if row.revision != payload.revision:
                raise HTTPException(409, "This lead changed. Refresh and review the latest version.")
            if row.state == "delivered" and command != "suppress":
                raise HTTPException(409, "Simulated delivery is final. The sent version is retained.")
            data = dict(row.data)
            values = {"revision": row.revision + 1}
            detail = payload.reason.strip()
            if command == "suppress":
                values.update(suppressed=True, state="blocked", approved_hash=None)
                detail = detail or "User selected Do Not Contact. Approval revoked."
            elif row.suppressed:
                raise HTTPException(409, "Do Not Contact is active. Outreach actions are blocked.")
            elif command == "edit":
                if data["hold"]:
                    raise HTTPException(409, "Resolve the evidence hold before creating outreach.")
                # Demo is intentionally restricted to reserved example.com recipients.
                if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@example\.com", payload.recipient):
                    raise HTTPException(422, "Demo recipients must use example.com.")
                data.update(recipient=payload.recipient, subject=payload.subject, body=payload.body)
                # Edits invalidate claim annotations as well as approval. A human must reassess all claims.
                data["claims"] = []
                data["edited"] = True
                values.update(data=data, state="needs_review", approved_hash=None)
                detail = "Draft edited. Prior approval and claim annotations invalidated; full human verification required."
            elif command == "approve":
                if row.state != "needs_review" or data["hold"] or not data["body"]:
                    raise HTTPException(409, "Only a reviewable draft can be approved.")
                if review_flags(data):
                    raise HTTPException(422, "Resolve the draft quality flags before approval.")
                values.update(state="approved", approved_hash=fingerprint(data))
                detail = "Local demo reviewer approved this exact recipient, message, and evidence version."
            elif command == "reject":
                if not detail:
                    raise HTTPException(422, "Add a rejection reason so the decision is useful.")
                values.update(state="rejected", approved_hash=None)
            elif command == "research":
                if not detail:
                    raise HTTPException(422, "Describe what evidence is missing.")
                data["research_question"] = detail
                values.update(data=data, state="research_needed", approved_hash=None)
                detail = "Research request recorded (no live research started); run separately for live leads: " + detail
            elif command == "simulate":
                if row.state != "approved" or row.approved_hash != fingerprint(data):
                    raise HTTPException(409, "Current draft has no matching approval.")
                values.update(state="delivered")
                detail = "SIMULATED delivery recorded. No email provider was contacted."
            else:
                raise HTTPException(404, "Unknown action.")
            # Compare-and-swap prevents stale concurrent commands from both succeeding.
            result = db.execute(update(Lead).where(Lead.id == lead_id, Lead.revision == payload.revision).values(**values))
            if result.rowcount != 1:
                db.rollback()
                raise HTTPException(409, "Concurrent change detected. Refresh before continuing.")
            db.add(Event(lead_id=lead_id, action=command, detail=detail,
                         timestamp=datetime.now(timezone.utc).isoformat()))
            db.commit()
            db.expire_all()
            return present(db.get(Lead, lead_id))

    @app.put("/api/leads/{lead_id}/draft")
    def edit(lead_id: str, payload: Edit):
        return change(lead_id, "edit", payload)

    @app.post("/api/leads/{lead_id}/{command}")
    def act(lead_id: str, command: str, payload: Action):
        if command not in {"approve", "reject", "research", "suppress", "simulate"}:
            raise HTTPException(404, "Unknown action.")
        return change(lead_id, command, payload)

    static = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def home():
        return FileResponse(static / "index.html")

    return app


app = create_app()
