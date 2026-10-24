from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace
from app.acquisition import interface
from app.acquisition.models import Candidate, Evidence
from app.acquisition.discovery import shortlist
from app.acquisition.models import DiscoveryRequest

PAYLOAD = {'seller_website':'https://seller.example.org', 'offering':'AI ops', 'ideal_customer_profile':'Industrial firms', 'max_results':5}

def client():
    app=FastAPI()
    app.include_router(interface.router)
    return TestClient(app)

def test_preview_remains_available_without_key(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    c=client()
    assert c.get('/acquisition').status_code==200
    assert c.post('/api/acquisition/preview',json=PAYLOAD).status_code==200

def test_no_research_from_page_views(monkeypatch):
    def forbidden(*a,**k): raise AssertionError('Research started without click')
    monkeypatch.setattr(interface,'discover_live',forbidden)
    c=client()
    assert c.get('/acquisition').status_code==200
    assert c.get('/acquisition/ui.js').status_code==200

def test_consent_required_before_openai_or_quota(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','fake')
    monkeypatch.setattr(interface,'_reserve_live_attempt',lambda: (_ for _ in ()).throw(AssertionError('should not reserve')))
    assert client().post('/api/acquisition/live',json=PAYLOAD).status_code==422

def test_no_key_fails_without_quota(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.setattr(interface,'_reserve_live_attempt',lambda: (_ for _ in ()).throw(AssertionError('should not reserve')))
    assert client().post('/api/acquisition/live',json={**PAYLOAD,'consent_to_api':True}).status_code==503

def test_live_response_stays_unapproved_and_does_not_write_leads(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','fake')
    monkeypatch.setattr(interface,'_reserve_live_attempt',lambda: None)
    import sys
    from types import SimpleNamespace
    monkeypatch.setitem(sys.modules,'openai',SimpleNamespace(OpenAI=lambda **kw: object()))
    c=Candidate('Example Industrial','example-industrial.org','Fit requires review',(Evidence('S1','https://example.org/a','Industry noted'),),('Budget unknown',))
    report=SimpleNamespace(shortlist=shortlist(DiscoveryRequest(**PAYLOAD),[c]),research_calls=1)
    monkeypatch.setattr(interface,'discover_live',lambda *args,**kwargs: report)
    r=client().post('/api/acquisition/live',json={**PAYLOAD,'consent_to_api':True})
    assert r.status_code==200
    data=r.json()
    assert data['mode']=='live_research_unverified'
    assert data['candidates'][0]['status']=='needs_human_review'
    assert 'approve' not in data and 'recipient' not in data

def test_quota_persists_between_connections(monkeypatch,tmp_path):
    monkeypatch.setenv('SIGNALDESK_ACQUISITION_USAGE_DB',str(tmp_path/'limits.sqlite3'))
    for _ in range(5): interface._reserve_live_attempt()
    from fastapi import HTTPException
    try: interface._reserve_live_attempt()
    except HTTPException as exc: assert exc.status_code==429
    else: raise AssertionError('quota did not enforce')
