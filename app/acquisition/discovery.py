"""Deterministic shortlisting; no scraping, API calls, contacts, or outreach.

Only present researcher-provided candidates. Never fabricate extra companies to
reach ten; each candidate remains unapproved until reviewed by a human.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit

from .models import Candidate, DiscoveryRequest


def canonical_domain(domain: str) -> str:
    """Normalize a company-domain identifier for duplicate detection."""
    p = urlsplit("https://" + domain.strip().lower())
    host = (p.hostname or "").rstrip(".")
    return host.removeprefix("www.")


@dataclass(frozen=True)
class Shortlist:
    candidates: tuple[Candidate, ...]
    excluded_duplicates: int
    considered: int
    source: str = "researcher_supplied_unverified"


def shortlist(request: DiscoveryRequest, candidates: list[Candidate] | tuple[Candidate, ...]) -> Shortlist:
    """Keep input order; exclude duplicates, seller's own domain, and excess.

    Input ordering is externally supplied, not a computed qualification score.
    This step validates *presence* of citations, not their factual sufficiency.
    """
    selected: list[Candidate] = []
    seen: set[str] = set()
    duplicates = 0
    seller = canonical_domain(urlsplit(request.seller_website).hostname or "")
    for candidate in candidates:
        key = canonical_domain(candidate.domain)
        if key == seller:
            continue
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        if len(selected) < request.max_results:
            selected.append(candidate)
    return Shortlist(tuple(selected), duplicates, len(candidates))
