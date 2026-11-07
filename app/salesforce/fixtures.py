"""Entirely fictional Lead rows. Reserved example domains; no customer PII."""
from __future__ import annotations

from .contract import LeadAssessment, assess_synthetic_lead


FICTIONAL_LEADS: tuple[dict, ...] = (
    {"Id": "00Q000000000001", "Company": "Northstar Advisory",
     "Website": "https://www.northstar.example/", "HasOptedOutOfEmail": False,
     "DoNotCall": False, "IsDeleted": False},
    {"Id": "00Q000000000002", "Company": "Summit Services",
     "Website": "summit.example", "HasOptedOutOfEmail": True,
     "DoNotCall": False, "IsDeleted": False},
    {"Id": "00Q000000000003", "Company": "Harbor Systems",
     "Website": "harbor.example", "HasOptedOutOfEmail": False,
     "DoNotCall": True, "IsDeleted": False},
    {"Id": "00Q000000000004", "Company": "Cedar Works",
     "Website": "cedar.example", "HasOptedOutOfEmail": False,
     "DoNotCall": False, "IsDeleted": True},
    {"Id": "00Q000000000005", "Company": "Pinecrest Solutions",
     "Website": "https://pinecrest.example/contact", "HasOptedOutOfEmail": False,
     "DoNotCall": False, "IsDeleted": False},
    {"Id": "00Q000000000006", "Company": "Meridian Logistics",
     "Website": "meridian.example", "HasOptedOutOfEmail": False,
     "DoNotCall": False},  # A missing deletion flag must not be treated as False.
    {"Id": "00Q000000000007", "Company": "Delta Platforms",
     "Website": "delta.example", "HasOptedOutOfEmail": False,
     "DoNotCall": False, "IsDeleted": False},
)


def run_fictional_fixture() -> tuple[LeadAssessment, ...]:
    return tuple(assess_synthetic_lead(row) for row in FICTIONAL_LEADS)


def summarize_fixture() -> dict[str, object]:
    results = run_fictional_fixture()
    return {
        "scope": "fictional_crm_fixture_only",
        "external_calls": 0,
        "crm_writes": 0,
        "outreach_messages_sent": 0,
        "synthetic_records": len(results),
        "review_required": sum(r.state == "review_required" for r in results),
        "blocked": sum(r.state == "blocked" for r in results),
        "held": sum(r.state == "hold" for r in results),
        "decisions": [r.to_dict() for r in results],
    }
