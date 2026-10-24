"""Provider-mocked contract tests; do not use the network."""
import json
from types import SimpleNamespace as NS
import pytest
from app.acquisition.models import DiscoveryRequest
from app.acquisition.live_discovery import DiscoveryFailure, discover_live

URL = 'https://northstar.example.org/overview'

def req():
    return DiscoveryRequest('https://seller.example.org', 'AI consulting', 'Industrial manufacturers')

def payload(url=URL, count=1):
    return {'candidates': [
        {'company': f'Northstar {i}', 'domain': f'northstar{i}.example.org',
         'fit_reason': 'Industrial services described; interest unknown',
         'evidence': [{'source_id': 'S1', 'url': url, 'finding': 'Public company page'}],
         'unknowns': ['No known buying intent']}
        for i in range(count)
    ]}

def reply(data=None, urls=(URL,), status='completed'):
    annotations = [NS(type='url_citation', url=u) for u in urls]
    return NS(status=status, output_text=json.dumps(payload() if data is None else data),
              output=[NS(content=[NS(annotations=annotations)])])

class FakeResponses:
    def __init__(self, response=None, exc=None):
        self.response = response or reply()
        self.exc = exc
        self.calls = []
    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc:
            raise self.exc
        return self.response

def client(response=None, exc=None):
    provider = FakeResponses(response, exc)
    return NS(responses=provider), provider

def test_happy_path_citations_human_review():
    api, calls = client()
    report = discover_live(req(), client=api)
    assert len(report.shortlist.candidates) == 1
    assert report.shortlist.candidates[0].status == 'needs_human_review'
    assert report.provider_verified is False
    assert len(calls.calls) == 1
    assert calls.calls[0]['max_tool_calls'] == 2
    assert calls.calls[0]['store'] is False
    assert len(calls.calls[0]['tools']) == 1

def test_no_provider_citations_fails_closed():
    api, _ = client(reply(urls=()))
    with pytest.raises(DiscoveryFailure): discover_live(req(), client=api)

def test_invented_citation_fails_closed():
    api, _ = client(reply(data=payload('https://unsupported.example.org/a')))
    with pytest.raises(DiscoveryFailure): discover_live(req(), client=api)

def test_empty_candidate_list_with_citation_is_safe():
    api, _ = client(reply(data={'candidates': []}))
    assert not discover_live(req(), client=api).shortlist.candidates

def test_malformed_json_fails_closed():
    response = reply()
    response.output_text = 'not-json'
    api, _ = client(response)
    with pytest.raises(DiscoveryFailure): discover_live(req(), client=api)

def test_too_many_fails_closed():
    api, _ = client(reply(data=payload(count=11)))
    with pytest.raises(DiscoveryFailure): discover_live(req(), client=api)

def test_incomplete_response_fails_closed():
    api, _ = client(reply(status='incomplete'))
    with pytest.raises(DiscoveryFailure): discover_live(req(), client=api)

def test_api_error_fails_closed():
    api, _ = client(exc=RuntimeError('test failure'))
    with pytest.raises(DiscoveryFailure): discover_live(req(), client=api)

def test_unsupported_fields_fail_closed():
    api, _ = client(reply(data={'candidates': [{'company': 'Foo'}]}))
    with pytest.raises(DiscoveryFailure): discover_live(req(), client=api)

def test_duplicate_company_domain_collapses():
    data = payload(count=2)
    data['candidates'][1]['domain'] = data['candidates'][0]['domain']
    api, _ = client(reply(data=data))
    assert len(discover_live(req(), client=api).shortlist.candidates) == 1
