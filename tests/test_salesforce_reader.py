"""Offline Salesforce REST tests; no actual external calls."""
import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
import pytest
from app.salesforce.reader import (
    SalesforceReadConfig, SalesforceReadError, preview_salesforce_leads,
)


class FakeResponse:
    status = 200
    def __init__(self, content):
        self.file = io.BytesIO(content if isinstance(content, bytes) else json.dumps(content).encode())
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
    def read(self, n=-1):
        return self.file.read(n)


class FakeOpener:
    def __init__(self, data=None, error=None):
        self.data, self.error, self.calls = data, error, []
    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return FakeResponse(self.data)


def config(**changes):
    kw = {"instance_url": "https://sandbox.my.salesforce.com",
          "access_token": "TEST_TOKEN_DO_NOT_EXPOSE"}
    kw.update(changes)
    return SalesforceReadConfig(**kw)


def lead(**changes):
    record = {"Id": "00Q000000000001", "Company": "Fictional Example",
              "Website": "example.org", "HasOptedOutOfEmail": False,
              "DoNotCall": False, "IsDeleted": False,
              "Email": "private@example.org"}
    record.update(changes)
    return record


def body(*records):
    return {"done": True, "totalSize": len(records), "records": list(records)}


def test_read_only_get_fixed_soql_and_redacted_summary():
    opener = FakeOpener(body(lead()))
    result = preview_salesforce_leads(config(), opener=opener)
    request, timeout = opener.calls[0]
    assert request.get_method() == "GET"
    url = urlsplit(request.full_url)
    assert url.scheme == "https"
    assert url.path == "/services/data/v66.0/query"
    assert parse_qs(url.query)["q"][0] == (
        "SELECT Id, Company, Website, HasOptedOutOfEmail, DoNotCall, IsDeleted "
        "FROM Lead ORDER BY CreatedDate DESC LIMIT 20"
    )
    assert timeout == 8
    assert request.get_header("Authorization") == "Bearer TEST_TOKEN_DO_NOT_EXPOSE"
    assert result.summary()["review_required"] == 1
    assert result.summary()["crm_writes"] == 0
    assert "private@example.org" not in json.dumps(result.summary())


def test_suppression_and_missing_fields_fail_closed():
    missing = lead()
    del missing["IsDeleted"]
    fake = FakeOpener(body(
        lead(), lead(DoNotCall=True), lead(HasOptedOutOfEmail=True),
        lead(IsDeleted=True), lead(Website=""), missing,
    ))
    report = preview_salesforce_leads(config(), opener=fake).summary()
    assert (report["review_required"], report["blocked"], report["held"]) == (1, 3, 2)
    assert report["approval_grants"] == report["outreach_sent"] == 0


@pytest.mark.parametrize("url", [
    "http://company.my.salesforce.com", "https://not-salesforce.example",
    "https://my.salesforce.com", "https://example.my.salesforce.com.evil.test",
    "https://user:pass@example.my.salesforce.com",
    "https://example.my.salesforce.com/a", "https://example.my.salesforce.com:88",
])
def test_untrusted_urls_rejected(url):
    with pytest.raises(ValueError):
        config(instance_url=url)


def test_bad_token_version_and_size():
    for token in ("", "has spaces", "bad\nnewline"):
        with pytest.raises(ValueError):
            config(access_token=token)
    with pytest.raises(ValueError):
        config(api_version="66.0/deletes")
    with pytest.raises(ValueError):
        config(max_records=51)


@pytest.mark.parametrize("status", [302, 401, 403, 429, 500])
def test_sanitized_http_errors_no_retry(status):
    fake = FakeOpener(error=HTTPError(
        "https://sandbox.my.salesforce.com", status, "TEST_TOKEN_DO_NOT_EXPOSE", {}, None
    ))
    with pytest.raises(SalesforceReadError) as err:
        preview_salesforce_leads(config(), opener=fake)
    assert "TEST_TOKEN_DO_NOT_EXPOSE" not in str(err.value)
    assert len(fake.calls) == 1


def test_network_error_redacted():
    fake = FakeOpener(error=URLError("TEST_TOKEN_DO_NOT_EXPOSE"))
    with pytest.raises(SalesforceReadError) as err:
        preview_salesforce_leads(config(), opener=fake)
    assert "TEST_TOKEN_DO_NOT_EXPOSE" not in str(err.value)


@pytest.mark.parametrize("bad", [
    {"done": False, "records": [lead()], "nextRecordsUrl": "/query/extra"},
    {"done": True, "records": [lead()], "nextRecordsUrl": "/query/extra"},
    {"done": True, "records": "bad"},
    {"done": True, "records": [lead()] * 21},
])
def test_partial_bad_payload_denied_without_followup(bad):
    fake = FakeOpener(bad)
    with pytest.raises(SalesforceReadError):
        preview_salesforce_leads(config(), opener=fake)
    assert len(fake.calls) == 1


@pytest.mark.parametrize("bad", [b"NOT_JSON", b"x" * 131073])
def test_invalid_or_oversized_response_denied(bad):
    with pytest.raises(SalesforceReadError):
        preview_salesforce_leads(config(), opener=FakeOpener(bad))


def test_unconfigured_environment_fails_before_network(monkeypatch):
    monkeypatch.delenv("SIGNALDESK_SF_INSTANCE_URL", raising=False)
    monkeypatch.delenv("SIGNALDESK_SF_ACCESS_TOKEN", raising=False)
    with pytest.raises(SalesforceReadError):
        SalesforceReadConfig.from_environment()
