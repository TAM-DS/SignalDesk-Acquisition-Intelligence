"""Offline provider-mock tests for fail-closed diagnostic categories."""
import json
from types import SimpleNamespace as NS
import pytest
from app.acquisition.live_discovery import discover_live, DiscoveryFailure
from app.acquisition.models import DiscoveryRequest

URL = 'https://evidence.example.org/a'
REQUEST = DiscoveryRequest('https://seller.example.org', 'AI operations', 'Industrial firms')


def fake_client(*, annotations=(), output_text=None, status='completed', error=None):
    data = {'candidates': [{'company': 'Example Firm', 'domain': 'example-firm.org',
            'fit_reason': 'Publicly described operations',
            'evidence': [{'source_id': 'S1', 'url': URL, 'finding': 'Operations described'}],
            'unknowns': ['Budget unknown']}]}
    response = NS(status=status, output_text=json.dumps(data) if output_text is None else output_text,
                  output=[NS(content=[NS(annotations=[NS(type='url_citation', url=u) for u in annotations])])])
    class Calls:
        def create(self, **kwargs):
            if error is not None:
                raise error
            return response
    return NS(responses=Calls())


def test_valid_json_without_provider_annotations_is_rejected():
    with pytest.raises(DiscoveryFailure) as err:
        discover_live(REQUEST, client=fake_client(annotations=()))
    assert err.value.code == 'missing_citations'


def test_provider_exception_categorized_without_raw_error_text():
    with pytest.raises(DiscoveryFailure) as err:
        discover_live(REQUEST, client=fake_client(error=RuntimeError('SECRET-MARKER-DO-NOT-LOG')))
    assert err.value.code == 'provider_error'
    assert err.value.provider_type == 'RuntimeError'
    assert 'SECRET-MARKER' not in str(err.value)


def test_invalid_citation_still_rejected():
    with pytest.raises(DiscoveryFailure) as err:
        discover_live(REQUEST, client=fake_client(annotations=['https://another.example.org/unrelated']))
    assert err.value.code == 'citation_mismatch'


def test_incomplete_provider_response_categorized():
    with pytest.raises(DiscoveryFailure) as err:
        discover_live(REQUEST, client=fake_client(status='incomplete', annotations=[URL]))
    assert err.value.code == 'incomplete_response'


def test_valid_citation_still_accepts_for_human_review():
    report = discover_live(REQUEST, client=fake_client(annotations=[URL]))
    assert report.shortlist.candidates[0].status == 'needs_human_review'
