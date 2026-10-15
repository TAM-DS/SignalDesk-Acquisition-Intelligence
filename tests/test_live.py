from types import SimpleNamespace as NS
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import create_app, Lead, ResearchRun
from app.live import research_and_draft, DraftAssessment, Claim, LiveFailure


PAYLOAD = {'company': 'Acme Services', 'domain': 'acmeservices.com', 'contact': 'Operations team',
           'seller': 'Test Consultancy', 'offer': 'We map reporting workflows and evaluate a bounded automation pilot.',
           'icp': 'B2B services with documented manual reporting workflows.', 'consent_to_api': True}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'not-a-real-key-for-mocked-tests')
    with TestClient(create_app(f"sqlite:///{tmp_path / 'live.db'}")) as c:
        yield c


def add(c):
    response = c.post('/api/leads', json=PAYLOAD)
    assert response.status_code == 200
    return response.json()


def generate(c, lead):
    return c.post(f'/api/leads/{lead["id"]}/generate', json={'revision': lead['revision']})


def row(c, id):
    return next(x for x in c.get('/api/leads').json() if x['id'] == id)


def result():
    return {'sources': [{'id': 'W1', 'url': 'https://acmeservices.com/about', 'synthetic': False}],
            'claims': [{'text': 'Manual reports', 'source_id': 'W1'}], 'subject': 'Reporting question',
            'body': 'Could a reporting review be useful?', 'hold': '', 'rationale': 'Business fit needs human review.',
            'usage': [{'input_tokens': 40, 'output_tokens': 20, 'web_search_calls': 1}], 'model': 'mock'}


def test_live_result_requires_human_approval(client, monkeypatch):
    monkeypatch.setattr('app.main.research_and_draft', lambda *args: result())
    lead = add(client)
    response = generate(client, lead)
    assert response.json()['state'] == 'needs_review'
    assert not response.json()['approval_matches']
    assert client.post(f'/api/leads/{lead["id"]}/simulate', json={'revision': response.json()['revision']}).status_code == 409


def test_fixtures_never_go_to_live_provider(client, monkeypatch):
    provider = Mock()
    monkeypatch.setattr('app.main.research_and_draft', provider)
    assert generate(client, row(client, 'avery')).status_code == 409
    provider.assert_not_called()


def test_missing_key_makes_no_change(client, monkeypatch):
    lead = add(client)
    monkeypatch.delenv('OPENAI_API_KEY')
    assert generate(client, lead).status_code == 503
    assert row(client, lead['id'])['revision'] == 1


def test_error_persists_hold_and_usage(client, monkeypatch):
    def fail(*args):
        raise LiveFailure('Provider timed out.', [{'input_tokens': 10}])
    monkeypatch.setattr('app.main.research_and_draft', fail)
    lead = add(client)
    assert generate(client, lead).status_code == 502
    assert row(client, lead['id'])['state'] == 'research_needed'
    runs = client.get(f'/api/leads/{lead["id"]}/runs').json()
    assert runs[0]['status'] == 'failed'
    assert runs[0]['usage'][0]['input_tokens'] == 10


def test_suppression_during_research_cannot_be_overwritten(client, monkeypatch):
    lead = add(client)
    def concurrent(*args):
        with Session(client.app.state.engine) as db:
            item = db.get(Lead, lead['id'])
            item.suppressed = True
            item.state = 'blocked'
            item.revision += 1
            db.commit()
        return result()
    monkeypatch.setattr('app.main.research_and_draft', concurrent)
    assert generate(client, lead).status_code == 409
    assert row(client, lead['id'])['state'] == 'blocked'
    assert row(client, lead['id'])['body'] == ''
    assert client.get(f'/api/leads/{lead["id"]}/runs').json()[0]['status'] == 'discarded'


def test_three_run_cap(client, monkeypatch):
    provider = Mock(return_value=result())
    monkeypatch.setattr('app.main.research_and_draft', provider)
    lead = add(client)
    for _ in range(3):
        assert generate(client, row(client, lead['id'])).status_code == 200
    assert generate(client, row(client, lead['id'])).status_code == 429
    assert provider.call_count == 3


@pytest.mark.parametrize('domain', ['localhost', '127.0.0.1', 'https://user:pass@acmeservices.com', 'example.com', 'acme.internal'])
def test_nonpublic_domains_rejected(client, domain):
    assert client.post('/api/leads', json={**PAYLOAD, 'domain': domain}).status_code == 422


def fake_provider(url='https://acmeservices.com/about', source_id='W1', contact_match=True):
    text = 'The company has manual reporting.'
    annotation = NS(type='url_citation', url=url, title='Company overview', start_index=len(text), end_index=len(text))
    research = NS(id='r1', status='completed', output_text=text, usage=NS(input_tokens=50, output_tokens=30),
                  output=[NS(type='web_search_call'), NS(type='message', content=[NS(type='output_text', text=text, annotations=[annotation])])])
    assessment = DraftAssessment(company_match=True, contact_match=contact_match, fit='yes', rationale='Fit', hold_reason='',
                                 subject='Question', body='Your team reports manually. Could a workflow review help?', claims=[Claim(text='Manual reporting', source_id=source_id)])
    draft = NS(id='r2', status='completed', output_parsed=assessment, usage=NS(input_tokens=80, output_tokens=40), output=[])
    return NS(responses=NS(create=Mock(return_value=research), parse=Mock(return_value=draft)))


def test_provider_uses_bounded_search_and_structured_draft():
    provider = fake_provider()
    output = research_and_draft(PAYLOAD, client=provider)
    assert output['body']
    args = provider.responses.create.call_args.kwargs
    assert args['max_tool_calls'] == 2 and args['store'] is False
    assert args['tools'][0]['filters']['allowed_domains'] == ['acmeservices.com']
    assert provider.responses.parse.call_args.kwargs['text_format'] is DraftAssessment


def test_external_citation_does_not_become_evidence():
    provider = fake_provider(url='https://untrusted.example/fake')
    output = research_and_draft(PAYLOAD, client=provider)
    assert output['hold'] and not output['body']
    provider.responses.parse.assert_not_called()


def test_invented_source_id_is_rejected():
    with pytest.raises(LiveFailure, match='unknown source'):
        research_and_draft(PAYLOAD, client=fake_provider(source_id='made-up'))


def test_uncertain_contact_blocks_draft():
    output = research_and_draft(PAYLOAD, client=fake_provider(contact_match=False))
    assert output['hold'] and not output['body']


def test_api_consent_required(client):
    assert client.post('/api/leads', json={**PAYLOAD, 'consent_to_api': False}).status_code == 422


def test_restart_recovers_interrupted_run(tmp_path):
    url = f"sqlite:///{tmp_path / 'restart.db'}"
    with TestClient(create_app(url)) as c:
        lead = add(c)
        with Session(c.app.state.engine) as db:
            item = db.get(Lead, lead['id'])
            item.state = 'researching'
            db.add(ResearchRun(id='interrupted', lead_id=item.id, revision=item.revision, status='running', created_at='2026-10-13', detail={}))
            db.commit()
    with TestClient(create_app(url)) as c:
        assert row(c, lead['id'])['state'] == 'research_needed'
        assert c.get(f'/api/leads/{lead["id"]}/runs').json()[0]['status'] == 'interrupted'


def test_recorded_evidence_question_reaches_next_live_run(client, monkeypatch):
    provider = Mock(return_value=result())
    monkeypatch.setattr('app.main.research_and_draft', provider)
    lead = add(client)
    question = 'Verify the contact still leads operations.'
    response = client.post(f'/api/leads/{lead["id"]}/research', json={'revision': lead['revision'], 'reason': question})
    assert response.status_code == 200
    assert generate(client, response.json()).status_code == 200
    assert provider.call_args.args[1] == question


def test_live_reference_does_not_present_generated_prose_as_source_excerpt():
    provider = fake_provider()
    part = provider.responses.create.return_value.output[1].content[0]
    part.text = 'Unrelated invented seller history. ' + 'x' * 500
    part.annotations[0].start_index = len(part.text)
    output = research_and_draft(PAYLOAD, client=provider)
    source = output['sources'][0]
    assert source['url'] == 'https://acmeservices.com/about'
    assert 'Unrelated' not in source['excerpt']
    assert 'xxxxx' not in source['excerpt']
    assert 'verify' in source['excerpt']


def test_gpt5_budget_and_reasoning_preserved(monkeypatch):
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-5-mini')
    provider = fake_provider()
    research_and_draft(PAYLOAD, client=provider)
    for call in (provider.responses.create, provider.responses.parse):
        args = call.call_args.kwargs
        assert args['max_output_tokens'] == 4000
        assert args['reasoning'] == {'effort': 'low'}


def test_incomplete_research_records_usage_and_skips_drafting():
    provider = fake_provider()
    response = provider.responses.create.return_value
    response.status = 'incomplete'
    response.incomplete_details = NS(reason='max_output_tokens')
    with pytest.raises(LiveFailure, match='max_output_tokens') as failure:
        research_and_draft(PAYLOAD, client=provider)
    assert failure.value.usage[0]['response_id'] == 'r1'
    provider.responses.parse.assert_not_called()
