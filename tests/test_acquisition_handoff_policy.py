"""Offline policy tests: no database or provider calls."""
from app.acquisition.handoff import canonical_domain, evaluate_handoff
from app.acquisition.models import Candidate, Evidence

CANDIDATE = Candidate(
    "Example Company", "example-company.org", "Potential fit; verify",
    (Evidence("S1", "https://example.org/source", "Provider reference only"),),
    ("Buying intent unknown",),
)

def decide(leads=(), approved=True, reviewed=True, contact="Operations department"):
    return evaluate_handoff(
        CANDIDATE, leads, approved_by_human=approved,
        evidence_reviewed=reviewed, contact=contact,
    )

def test_human_approval_required():
    assert not decide(approved=False).allowed

def test_source_review_required():
    assert not decide(reviewed=False).allowed

def test_contact_cannot_be_invented_or_omitted():
    assert not decide(contact=" ").allowed

def test_block_suppressed_domain_even_with_www_case_variation():
    result = decide([{"domain": "WWW.Example-Company.org", "suppressed": True}])
    assert not result.allowed
    assert "Do Not Contact" in result.reason

def test_existing_unsuppressed_lead_is_duplicate():
    result = decide([{"domain": "https://example-company.org", "suppressed": False}])
    assert not result.allowed
    assert "already exists" in result.reason

def test_fail_closed_when_existing_leads_missing_required_domain():
    assert not decide([{"suppressed": False}]).allowed

def test_reviewed_and_distinct_company_can_proceed_to_controlled_creation():
    result = decide([{"domain": "other-company.org", "suppressed": False}])
    assert result.allowed
    assert "research_needed" in result.reason

def test_domain_normalization_is_conservative():
    assert canonical_domain("https://WWW.Example-Company.org/") == "example-company.org"
