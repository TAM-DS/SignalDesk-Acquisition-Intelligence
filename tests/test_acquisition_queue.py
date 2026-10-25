"""Phase 5B: persistent queue and human-authorized handoff, no provider calls."""
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

CANDIDATE = {
    "company": "Northstar Industrial",
    "domain": "northstar-industrial.org",
    "fit_reason": "Potential industrial fit, not proven",
    "evidence": [{"source_id": "S1", "url": "https://example.org/industry",
                  "finding": "Industry description requires human checking"}],
    "unknowns": ["Budget", "Intent"],
}
HANDOFF = {"contact": "Operations department", "seller": "Example Seller",
           "offer": "Proposed AI operations workflow improvement services",
           "icp": "Industrial operations organizations", "confirm_create": True}

@pytest.fixture()
def api(tmp_path):
    app = create_app("sqlite:///" + str(tmp_path / "test.db"))
    with TestClient(app) as client:
        yield client

def queued(api):
    r = api.post("/api/acquisition/queue", json=CANDIDATE)
    assert r.status_code == 201, r.text
    return r.json()["id"]

def test_queue_persists_and_never_auto_approves(api):
    q = queued(api)
    row = next(x for x in api.get("/api/acquisition/queue").json() if x["id"] == q)
    assert row["state"] == "pending"
    assert row["lead_id"] is None

def test_queue_prevents_domain_duplicates(api):
    queued(api)
    assert api.post("/api/acquisition/queue", json=CANDIDATE).status_code == 409

def test_no_handoff_before_review(api):
    q = queued(api)
    assert api.post(f"/api/acquisition/queue/{q}/handoff", json=HANDOFF).status_code == 409

def test_approval_requires_evidence_review(api):
    q = queued(api)
    r = api.post(f"/api/acquisition/queue/{q}/decision",
                 json={"approve": True, "evidence_reviewed": False, "note": "Looks fine"})
    assert r.status_code == 422

def test_rejected_candidate_never_transfers(api):
    q = queued(api)
    assert api.post(f"/api/acquisition/queue/{q}/decision",
                    json={"approve": False, "note": "Not appropriate"}).status_code == 200
    assert api.post(f"/api/acquisition/queue/{q}/handoff", json=HANDOFF).status_code == 409

def test_handoff_requires_explicit_confirmation(api):
    q = queued(api)
    api.post(f"/api/acquisition/queue/{q}/decision",
             json={"approve": True, "evidence_reviewed": True, "note": "Checked reference"})
    assert api.post(f"/api/acquisition/queue/{q}/handoff",
                    json={**HANDOFF, "confirm_create": False}).status_code == 422

def test_handoff_creates_review_only_lead_without_outreach(api):
    q = queued(api)
    api.post(f"/api/acquisition/queue/{q}/decision",
             json={"approve": True, "evidence_reviewed": True, "note": "Checked reference"})
    r = api.post(f"/api/acquisition/queue/{q}/handoff", json=HANDOFF)
    assert r.status_code == 201, r.text
    assert r.json()["state"] == "research_needed"
    lead = next(x for x in api.get("/api/leads").json() if x["id"] == r.json()["lead_id"])
    assert lead["state"] == "research_needed"
    assert lead["body"] == ""
    assert lead["sources"] == []
    assert api.post(f"/api/acquisition/queue/{q}/handoff", json=HANDOFF).status_code == 409

def test_existing_lead_domain_blocks_handoff(api):
    q = queued(api)
    api.post(f"/api/acquisition/queue/{q}/decision",
             json={"approve": True, "evidence_reviewed": True, "note": "Reviewed"})
    from sqlalchemy.orm import Session
    from app.main import Lead
    with Session(api.app.state.engine) as db:
        db.add(Lead(id="preexisting", data={"domain": CANDIDATE["domain"]},
                    state="blocked", revision=1, suppressed=True))
        db.commit()
    r = api.post(f"/api/acquisition/queue/{q}/handoff", json=HANDOFF)
    assert r.status_code == 409
    assert "Do Not Contact" in r.json()["detail"]
