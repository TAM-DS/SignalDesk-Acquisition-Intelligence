"""Strict offline classification of fictional Salesforce Lead snapshots.

This does NOT connect to Salesforce or create leads. Every result is either a
hold, a block, or a *request for review*, never permission to act. The narrow
output intentionally excludes contact names, emails and phone numbers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import ipaddress
import re
from typing import Any, Mapping
from urllib.parse import urlsplit


@dataclass(frozen=True)
class LeadAssessment:
    crm_id: str | None
    company: str | None
    domain: str | None
    state: str
    reason: str
    source: str = "fictional_crm_fixture"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def company_domain(value: object) -> str | None:
    """Normalize one public-looking hostname. This function NEVER fetches it."""
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if any(c.isspace() for c in raw):
        return None
    try:
        parsed = urlsplit(raw if "://" in raw else "https://" + raw)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return None
        if parsed.username or parsed.password or parsed.port is not None:
            return None
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            return None
        hostname = parsed.hostname.lower().rstrip(".")
        if hostname.startswith("www."):
            hostname = hostname[4:]
        if hostname == "localhost" or "." not in hostname or len(hostname) > 253:
            return None
        try:
            ipaddress.ip_address(hostname)
            return None
        except ValueError:
            pass
        labels = hostname.split(".")
        if not all(
            1 <= len(label) <= 63
            and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
            for label in labels
        ):
            return None
        if len(labels[-1]) < 2:
            return None
        return hostname
    except (ValueError, UnicodeError):
        return None


def assess_synthetic_lead(record: Mapping[str, Any] | None) -> LeadAssessment:
    """Return a *review candidate*, never approval or an outreach permission.

    Fail closed when deletion/opt-out flags were not retrieved or have unknown
    values; a real integration must also re-check Salesforce permissions and
    current suppression state before any change.
    """
    if not isinstance(record, Mapping):
        return LeadAssessment(None, None, None, "hold", "CRM record is invalid.")
    value_id = record.get("Id")
    crm_id = (
        value_id
        if isinstance(value_id, str)
        and re.fullmatch(r"[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?", value_id)
        else None
    )
    value_company = record.get("Company")
    company = (
        value_company.strip()
        if isinstance(value_company, str) and 0 < len(value_company.strip()) <= 160
        else None
    )
    if crm_id is None or company is None:
        return LeadAssessment(crm_id, company, None, "hold", "CRM identity or company is incomplete.")

    required_flags = ("HasOptedOutOfEmail", "DoNotCall", "IsDeleted")
    if any(type(record.get(flag)) is not bool for flag in required_flags):
        return LeadAssessment(crm_id, company, None, "hold", "Opt-out or deletion evidence is absent or invalid.")
    if any(record[flag] for flag in required_flags):
        return LeadAssessment(crm_id, company, None, "blocked", "CRM suppression or deletion restriction.")

    domain = company_domain(record.get("Website"))
    if domain is None:
        return LeadAssessment(crm_id, company, None, "hold", "Verified company domain is missing.")
    return LeadAssessment(
        crm_id, company, domain, "review_required",
        "Human evidence review and fresh suppression check required.",
    )
