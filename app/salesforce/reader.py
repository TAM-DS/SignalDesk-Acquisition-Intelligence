"""Salesforce read-only preview; no writes, persistence, outreach or Agentforce calls."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .contract import assess_synthetic_lead, LeadAssessment


class SalesforceReadError(Exception):
    """Safe message: never show token, URL error detail, or CRM response body."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class SalesforceReadConfig:
    instance_url: str
    access_token: str
    api_version: str = "66.0"
    max_records: int = 20

    def __post_init__(self):
        try:
            parsed = urlsplit(self.instance_url)
            host = (parsed.hostname or "").lower()
            port = parsed.port
        except (ValueError, AttributeError):
            raise ValueError("Salesforce HTTPS My Domain instance is required.") from None
        if (
            parsed.scheme != "https"
            or not host.endswith(".my.salesforce.com")
            or host == "my.salesforce.com"
            or parsed.username or parsed.password or port is not None
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment
            or any(char.isspace() for char in self.instance_url)
        ):
            raise ValueError("Salesforce HTTPS My Domain instance is required.")
        if not isinstance(self.access_token, str) or not self.access_token or any(
            char.isspace() for char in self.access_token
        ):
            raise ValueError("A valid OAuth access token is required.")
        if not re.fullmatch(r"\d{2}\.\d", self.api_version):
            raise ValueError("Invalid REST API version.")
        if type(self.max_records) is not int or not 1 <= self.max_records <= 50:
            raise ValueError("Preview size must be between 1 and 50.")

    @classmethod
    def from_environment(cls):
        instance = os.getenv("SIGNALDESK_SF_INSTANCE_URL")
        token = os.getenv("SIGNALDESK_SF_ACCESS_TOKEN")
        if not instance or not token:
            raise SalesforceReadError("Dev-org CRM preview is not configured.")
        try:
            return cls(instance, token, os.getenv("SIGNALDESK_SF_API_VERSION", "66.0"))
        except ValueError:
            raise SalesforceReadError("CRM preview configuration rejected.") from None


@dataclass(frozen=True)
class SalesforceLeadPreview:
    decisions: tuple[LeadAssessment, ...]

    def summary(self):
        return {
            "source": "salesforce_rest_read_only", "records_assessed": len(self.decisions),
            "review_required": sum(x.state == "review_required" for x in self.decisions),
            "blocked": sum(x.state == "blocked" for x in self.decisions),
            "held": sum(x.state == "hold" for x in self.decisions),
            "crm_writes": 0, "approval_grants": 0, "outreach_sent": 0,
            "disclaimer": "Not proof of verified lead fit, CRM write permission, or customer ROI.",
        }


def preview_salesforce_leads(
    config: SalesforceReadConfig, *, opener: Any = None, timeout_seconds: float = 8.0
) -> SalesforceLeadPreview:
    """One bounded GET using a fixed SOQL string; no retries or pagination.

    Use ONLY an authorized Salesforce developer org with fictional records.
    A My Domain hostname cannot by itself prove that an org is non-production.
    """
    if not 0 < timeout_seconds <= 30:
        raise ValueError("Timeout outside approved range.")
    soql = (
        "SELECT Id, Company, Website, HasOptedOutOfEmail, DoNotCall, IsDeleted "
        f"FROM Lead ORDER BY CreatedDate DESC LIMIT {config.max_records}"
    )
    url = (
        config.instance_url.rstrip("/")
        + f"/services/data/v{config.api_version}/query?q="
        + quote(soql, safe="")
    )
    request = Request(
        url, method="GET",
        headers={"Authorization": f"Bearer {config.access_token}", "Accept": "application/json"},
    )
    client = opener if opener is not None else build_opener(NoRedirect())
    try:
        with client.open(request, timeout=timeout_seconds) as response:
            if getattr(response, "status", 200) != 200:
                raise SalesforceReadError("CRM read did not succeed.")
            raw = response.read(131073)
    except HTTPError as err:
        if err.code in (301, 302, 303, 307, 308):
            raise SalesforceReadError("CRM redirect denied.") from None
        if err.code in (401, 403):
            raise SalesforceReadError("CRM authentication or permissions denied.") from None
        if err.code == 429:
            raise SalesforceReadError("CRM rate limit reached; no automatic retry.") from None
        raise SalesforceReadError(f"CRM read returned HTTP {err.code}.") from None
    except (URLError, OSError, TimeoutError):
        raise SalesforceReadError("CRM read failed; no automatic retry.") from None
    if len(raw) > 131072:
        raise SalesforceReadError("CRM response is too large.")
    try:
        body = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise SalesforceReadError("CRM response was not valid JSON.") from None
    if (
        not isinstance(body, dict) or body.get("done") is not True
        or not isinstance(body.get("records"), list)
        or len(body["records"]) > config.max_records or body.get("nextRecordsUrl")
    ):
        raise SalesforceReadError("CRM response incomplete or unexpected; fail-closed.")
    decisions = tuple(
        replace(assess_synthetic_lead(row), source="salesforce_rest_read_only")
        for row in body["records"]
    )
    return SalesforceLeadPreview(decisions)
