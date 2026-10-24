"""Acquisition contract and shortlisting tests. All examples are fictional."""
import pytest
from app.acquisition.discovery import shortlist
from app.acquisition.models import Candidate, DiscoveryRequest, Evidence


def request(limit=10):
    return DiscoveryRequest("https://seller.example.com", "Proposed consulting services", "Manufacturers", limit)


def candidate(name="Example Manufacturing", domain="manufacturer.example.com"):
    return Candidate(name, domain, "Potential industry match; requires human verification", (
        Evidence("S1", "https://manufacturer.example.com/about", "Public page reportedly describes manufacturing"),
    ), ("Buying intent unknown",))


def test_valid_shortlist_never_claims_approval():
    result = shortlist(request(), [candidate()])
    assert len(result.candidates) == 1
    assert result.candidates[0].status == "needs_human_review"
    assert result.source == "researcher_supplied_unverified"


def test_empty_is_not_filled_with_invented_prospects():
    assert shortlist(request(), []).candidates == ()


def test_duplicate_domains_are_suppressed():
    result = shortlist(request(), [candidate(), candidate("Same company", "www.manufacturer.example.com")])
    assert len(result.candidates) == 1
    assert result.excluded_duplicates == 1


def test_seller_is_not_a_prospect():
    assert not shortlist(request(), [candidate(domain="seller.example.com")]).candidates


def test_limit_ten():
    cs = [candidate(f"Company {i}", f"company{i}.example.com") for i in range(15)]
    result = shortlist(request(), cs)
    assert len(result.candidates) == 10
    assert result.considered == 15


def test_custom_limit():
    cs = [candidate(f"Company {i}", f"company{i}.example.com") for i in range(5)]
    assert len(shortlist(request(2), cs).candidates) == 2


@pytest.mark.parametrize("limit", [0, 11, -1])
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        request(limit)


@pytest.mark.parametrize("url", ["http://localhost/private", "file:///etc/passwd", "https://127.0.0.1/", "https://user:pass@example.com", "https://x.local/"])
def test_unacceptable_source_urls(url):
    with pytest.raises(ValueError):
        Evidence("S1", url, "Research finding")


def test_missing_citation_not_allowed():
    with pytest.raises(ValueError):
        Candidate("Example", "example.com", "Potential fit", ())


def test_duplicate_source_ids_not_allowed():
    with pytest.raises(ValueError):
        e = Evidence("S1", "https://example.com/a", "One")
        Candidate("Example", "example.com", "Potential fit", (e, e))


def test_no_automatic_outreach_capability():
    result = shortlist(request(), [candidate()])
    assert not hasattr(result, "send")
    assert not hasattr(result, "approve")
