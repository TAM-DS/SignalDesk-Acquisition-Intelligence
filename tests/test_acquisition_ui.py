from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.acquisition.interface import router


def client():
    app=FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_page_and_assets():
    c=client()
    assert c.get('/acquisition').status_code == 200
    assert b'Preview uses fictional examples and makes no API calls.' in c.get('/acquisition').content
    assert c.get('/acquisition/ui.css').status_code == 200
    assert c.get('/acquisition/ui.js').status_code == 200


def test_fictional_shortlist_is_bounded_and_has_evidence():
    c=client()
    p={'seller_website':'https://example.com','offering':'Services','ideal_customer_profile':'Operations','max_results':1}
    r=c.post('/api/acquisition/preview',json=p)
    assert r.status_code==200
    x=r.json()
    assert x['mode']=='fictional_preview_only'
    assert len(x['candidates'])==1
    assert x['candidates'][0]['evidence']
    assert x['candidates'][0]['status']=='needs_human_review'


def test_reject_invalid_form():
    c=client()
    p={'seller_website':'http://localhost','offering':'Services','ideal_customer_profile':'Operations','max_results':10}
    assert c.post('/api/acquisition/preview',json=p).status_code==422
    p['seller_website']='https://example.com';p['max_results']=11
    assert c.post('/api/acquisition/preview',json=p).status_code==422


def test_not_automatically_connected_to_delivery():
    c=client()
    paths = {route.path for route in c.app.routes if hasattr(route, "path")}
    assert not any('approve' in x or 'deliver' in x or 'generate' in x for x in paths)
