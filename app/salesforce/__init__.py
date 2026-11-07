"""Salesforce-oriented, offline reference contracts (no live CRM access)."""
from .contract import LeadAssessment, assess_synthetic_lead, company_domain

__all__ = ["LeadAssessment", "assess_synthetic_lead", "company_domain"]
