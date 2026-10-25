"""Strict, provider-independent contracts for acquisition research.

An evidence URL is a traceable citation, NOT proof that the cited claim is true.
"""
from dataclasses import dataclass, field
from urllib.parse import urlsplit
import ipaddress


def public_http_url(value: str) -> bool:
    """Reject malformed/obviously local links; not a full SSRF defense.

    No URL is fetched by this module. Future network clients must independently
    enforce DNS/IP resolution policy and redirect restrictions.
    """
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        return False
    try:
        p = urlsplit(value)
        if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
            return False
        host = p.hostname.rstrip(".").lower()
        if host in ("localhost",) or host.endswith((".local", ".localhost", ".internal")):
            return False
        try:
            address = ipaddress.ip_address(host)
            return address.is_global
        except ValueError:
            return "." in host and not host.startswith(".") and not host.endswith(".")
    except ValueError:
        return False


@dataclass(frozen=True)
class Evidence:
    source_id: str
    url: str
    finding: str

    def __post_init__(self):
        if not self.source_id.strip() or not self.finding.strip():
            raise ValueError("Every evidence item needs a source ID and finding")
        if not public_http_url(self.url):
            raise ValueError("Evidence requires a public HTTP(S) citation URL")


@dataclass(frozen=True)
class Candidate:
    company: str
    domain: str
    fit_reason: str
    evidence: tuple[Evidence, ...]
    unknowns: tuple[str, ...] = ()
    status: str = field(default="needs_human_review", init=False)

    def __post_init__(self):
        if not all(isinstance(x, str) and x.strip() for x in (self.company, self.domain, self.fit_reason)):
            raise ValueError("Company, domain and fit reason are required")
        if not public_http_url("https://" + self.domain.strip().lower()):
            raise ValueError("A valid public company domain is required")
        if not self.evidence:
            raise ValueError("Every candidate requires at least one citation")
        ids = [item.source_id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("Evidence IDs must be unique within a candidate")


@dataclass(frozen=True)
class DiscoveryRequest:
    seller_website: str
    offering: str
    ideal_customer_profile: str
    max_results: int = 10

    def __post_init__(self):
        if not public_http_url(self.seller_website):
            raise ValueError("Seller website must be a public HTTP(S) URL")
        if not self.offering.strip() or not self.ideal_customer_profile.strip():
            raise ValueError("Offering and ideal customer profile are required")
        if not 1 <= self.max_results <= 10:
            raise ValueError("max_results must be between 1 and 10")
