"""Offline tests for provider-returned web-search source metadata."""
from types import SimpleNamespace as NS

import pytest

from app.acquisition.live_discovery import DiscoveryFailure, discover_live
from test_acquisition_live import URL, client, reply, req, payload


def with_sources(urls, *, tool_type="web_search_call", source_type="url"):
    response = reply(urls=())
    response.output.append(NS(
        type=tool_type,
        action=NS(
            type="search",
            sources=[NS(type=source_type, url=url) for url in urls],
        ),
    ))
    return response


def test_provider_sources_are_requested():
    api, calls = client()
    discover_live(req(), client=api)
    assert calls.calls[0]["include"] == [
        "web_search_call.action.sources"
    ]


def test_real_provider_source_can_support_candidate_reference():
    api, _ = client(with_sources([URL]))
    report = discover_live(req(), client=api)
    assert len(report.shortlist.candidates) == 1
    assert report.shortlist.candidates[0].status == "needs_human_review"
    assert report.provider_verified is False


def test_invented_candidate_url_remains_blocked():
    response = with_sources([URL])
    response.output_text = __import__("json").dumps(
        payload("https://unsupported.example.org/fabricated")
    )
    api, _ = client(response)
    with pytest.raises(DiscoveryFailure) as err:
        discover_live(req(), client=api)
    assert err.value.code == "citation_mismatch"


def test_non_web_search_sources_are_not_trusted():
    api, _ = client(with_sources([URL], tool_type="message"))
    with pytest.raises(DiscoveryFailure) as err:
        discover_live(req(), client=api)
    assert err.value.code == "missing_citations"


def test_non_url_sources_are_not_trusted():
    api, _ = client(with_sources([URL], source_type="file"))
    with pytest.raises(DiscoveryFailure) as err:
        discover_live(req(), client=api)
    assert err.value.code == "missing_citations"


def test_no_source_metadata_still_fails_closed():
    api, _ = client(reply(urls=()))
    with pytest.raises(DiscoveryFailure) as err:
        discover_live(req(), client=api)
    assert err.value.code == "missing_citations"
