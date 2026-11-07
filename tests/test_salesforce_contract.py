"""Safety-focused, offline tests of the proposed Salesforce contract."""
from dataclasses import asdict

from app.salesforce import assess_synthetic_lead, company_domain
from app.salesforce.fixtures import FICTIONAL_LEADS, summarize_fixture


def make_lead(**changes):
    row = {
        "Id": "00Q000000000001",
        "Company": "Example Industries",
        "Website": "https://WWW.example.org/",
        "HasOptedOutOfEmail": False,
        "DoNotCall": False,
        "IsDeleted": False,
        "Email": "confidential@example.org",
        "Phone": "1234567890",
    }
    row.update(changes)
    return row


def test_valid_record_requests_review_never_creates_approval():
    result = assess_synthetic_lead(make_lead())
    assert result.state == "review_required"
    assert result.domain == "example.org"
    assert "approved" not in asdict(result)
    assert "confidential@example.org" not in str(asdict(result))


def test_opt_out_and_do_not_call_and_deleted_each_block():
    for flag in ("HasOptedOutOfEmail", "DoNotCall", "IsDeleted"):
        assert assess_synthetic_lead(make_lead(**{flag: True})).state == "blocked"


def test_missing_opt_out_or_deletion_evidence_holds():
    for flag in ("HasOptedOutOfEmail", "DoNotCall", "IsDeleted"):
        row = make_lead()
        del row[flag]
        assert assess_synthetic_lead(row).state == "hold"


def test_unknown_flags_do_not_coerce_to_false():
    assert assess_synthetic_lead(make_lead(DoNotCall="false")).state == "hold"
    assert assess_synthetic_lead(make_lead(IsDeleted=0)).state == "hold"


def test_company_and_salesforce_identity_required():
    assert assess_synthetic_lead(make_lead(Id="not-a-salesforce-id")).state == "hold"
    assert assess_synthetic_lead(make_lead(Company="")).state == "hold"
    assert assess_synthetic_lead(make_lead(Company="a" * 161)).state == "hold"


def test_record_must_be_mapping():
    assert assess_synthetic_lead(None).state == "hold"
    assert assess_synthetic_lead(["fake"]).state == "hold"


def test_reject_non_company_urls_and_hostnames():
    for host in (
        "https://example.org/restricted", "https://example.org/?secret=x",
        "http://localhost", "http://127.0.0.1",
        "ftp://example.org", "https://user:password@example.org",
        "https://example.org:8443", "https://abc..example",
    ):
        assert company_domain(host) is None


def test_normalize_public_company_domain_without_requests():
    assert company_domain("https://WWW.example.org/") == "example.org"
    assert company_domain("EXAMPLE.org") == "example.org"


def test_does_not_mutate_input_or_leak_contact_data():
    row = make_lead()
    before = dict(row)
    assert assess_synthetic_lead(row) == assess_synthetic_lead(row)
    assert row == before
    assert "Email" not in asdict(assess_synthetic_lead(row))
    assert "Phone" not in asdict(assess_synthetic_lead(row))


def test_fictional_demo_summary_is_reproducible_and_no_side_effects():
    first = summarize_fixture()
    second = summarize_fixture()
    assert first == second
    assert first["synthetic_records"] == len(FICTIONAL_LEADS) == 7
    assert first["review_required"] == 2
    assert first["blocked"] == 3
    assert first["held"] == 2
    assert first["external_calls"] == first["crm_writes"] == first["outreach_messages_sent"] == 0
