"""Pure, fail-closed handoff policy for acquisition candidates.

No DB writes, API calls, lead creation, or outreach occur in this module.
The caller must independently persist a reviewer decision and enforce this
policy again inside the lead-creation database transaction.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit

from .models import Candidate


@dataclass(frozen=True)
class HandoffDecision:
    allowed: bool
    reason: str


def canonical_domain(value: str) -> str:
    """Normalize host-only identifiers for exact company-domain comparison."""
    raw = value.strip().lower().rstrip(".")
    parsed = urlsplit(raw if "://" in raw else "https://" + raw)
    host = (parsed.hostname or "").rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if not host or parsed.username or parsed.password or parsed.port:
        raise ValueError("Invalid company domain")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("Expected a company domain, not a URL path")
    return host


def evaluate_handoff(
    candidate: Candidate,
    existing_leads,
    *,
    approved_by_human: bool,
    evidence_reviewed: bool,
    contact: str,
) -> HandoffDecision:
    """Deny until review, contact, and existing-lead checks all succeed.

    existing_leads contains dicts with domain and suppressed fields; the caller
    must supply ALL leads, including blocked/suppressed and delivered leads.
    """
    if not approved_by_human:
        return HandoffDecision(False, "A human must explicitly approve the candidate.")
    if not evidence_reviewed:
        return HandoffDecision(False, "A human must verify the supporting evidence.")
    if not contact or not contact.strip():
        return HandoffDecision(False, "A real contact or department is required; never invent one.")
    try:
        domain = canonical_domain(candidate.domain)
        existing = [(canonical_domain(item["domain"]), bool(item.get("suppressed"))) for item in existing_leads]
    except (KeyError, TypeError, AttributeError, ValueError):
        return HandoffDecision(False, "Unable to verify existing-lead and suppression state.")
    if any(host == domain and suppressed for host, suppressed in existing):
        return HandoffDecision(False, "Do Not Contact: this company domain is suppressed.")
    if any(host == domain for host, _ in existing):
        return HandoffDecision(False, "A lead for this company domain already exists.")
    return HandoffDecision(True, "Eligible for human-authorized creation in research_needed state.")
