"""Behavioral tests for authority boundaries and persisted decisions."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.main import Lead, create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'test.db'}")) as client:
        yield client


def get(client, id="avery"):
    return next(x for x in client.get('/api/leads').json() if x['id'] == id)


def act(client, command, id="avery", **kw):
    return client.post(f'/api/leads/{id}/{command}', json={"revision": get(client, id)['revision'], **kw})


def test_no_delivery_without_approval(client):
    assert act(client, 'simulate').status_code == 409
    assert get(client)['state'] == 'needs_review'


def test_approved_delivery_is_simulated_and_idempotent(client):
    assert act(client, 'approve').status_code == 200
    assert act(client, 'simulate').json()['state'] == 'delivered'
    assert act(client, 'simulate').json()['idempotent']
    events = client.get('/api/leads/avery/events').json()
    assert len([x for x in events if x['action'] == 'simulate']) == 1
    assert client.get('/api/workspace').json()['delivery'] == 'simulated_only'


def test_edit_revokes_approval_and_claim_links(client):
    act(client, 'approve')
    row = get(client)
    response = client.put('/api/leads/avery/draft', json={"revision": row['revision'], "recipient": row['recipient'], "subject": "Revised subject", "body": row['body']})
    assert response.status_code == 200
    assert response.json()['state'] == 'needs_review'
    assert response.json()['claims'] == []
    assert not response.json()['approval_matches']
    assert act(client, 'simulate').status_code == 409


def test_stale_reviewer_cannot_overwrite_new_decision(client):
    revision = get(client)['revision']
    act(client, 'reject', reason='Not relevant enough')
    assert client.post('/api/leads/avery/approve', json={"revision": revision}).status_code == 409


def test_suppression_revokes_existing_approval(client):
    act(client, 'approve')
    assert act(client, 'suppress').json()['suppressed']
    assert act(client, 'simulate').status_code == 409
    assert act(client, 'approve').status_code == 409


def test_seeded_do_not_contact_cannot_be_approved(client):
    assert act(client, 'approve', 'taylor').status_code == 409
    assert act(client, 'simulate', 'taylor').status_code == 409


@pytest.mark.parametrize('id', ['riley', 'sam', 'casey', 'devon'])
def test_evidence_hold_blocks_approval(client, id):
    assert act(client, 'approve', id).status_code == 409


def test_research_request_is_recorded_not_faked(client):
    response = act(client, 'research', reason='Confirm the business need')
    assert response.json()['state'] == 'research_needed'
    events = client.get('/api/leads/avery/events').json()
    assert 'no live research' in events[0]['detail']
    assert act(client, 'approve').status_code == 409


def test_reject_requires_a_reason(client):
    assert act(client, 'reject').status_code == 422


def test_quality_flag_blocks_approval(client):
    row = get(client)
    response = client.put('/api/leads/avery/draft', json={"revision": row['revision'], "recipient": row['recipient'], "subject": row['subject'], "body": 'Dear X, I love watching your wife.'})
    assert response.status_code == 200
    assert 'Personal-life reference' in response.json()['flags']
    assert act(client, 'approve').status_code == 422


def test_real_recipient_is_not_accepted_in_demo(client):
    row = get(client)
    assert client.put('/api/leads/avery/draft', json={"revision": row['revision'], "recipient": 'person@real-company.org', "subject": row['subject'], "body": row['body']}).status_code == 422


def test_database_tampering_invalidates_approval(client):
    act(client, 'approve')
    with Session(client.app.state.engine) as db:
        row = db.get(Lead, 'avery')
        row.data = {**row.data, "body": 'Changed outside the review workflow'}
        db.commit()
    assert act(client, 'simulate').status_code == 409


def test_cross_origin_write_is_rejected(client):
    response = client.post('/api/leads/avery/approve', json={"revision": 1}, headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 403


def test_persistence_across_restart(tmp_path):
    url = f"sqlite:///{tmp_path / 'persist.db'}"
    with TestClient(create_app(url)) as client:
        act(client, 'suppress')
    with TestClient(create_app(url)) as client:
        assert get(client)['suppressed']
        assert len(client.get('/api/leads/avery/events').json()) == 1


def test_ui_and_security_headers(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'SignalDesk' in response.text
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert client.get('/static/app.js').status_code == 200
    assert client.get('/static/style.css').status_code == 200


def test_edit_cannot_bypass_validated_draft_endpoint(client):
    assert act(client, 'edit').status_code == 404
