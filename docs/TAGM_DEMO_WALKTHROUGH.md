# TAGM client demonstration | 12-minute walkthrough

**Purpose:** demonstrate architecture judgment and working controls. All examples
are fictional. Run each command from its own repository root using the project's
installed environment. No Salesforce credentials are needed for this walkthrough.

## 0:00–2:00 | Frame the buyer decision

Revenue sponsor: "Can we reduce lead-review effort while preserving suppression
and human authority?"

Risk sponsor: "Can we connect evidence without inventing relationships between
identities, institutions or cases?"

State the pilot decision, baseline measurement and accountable owner before
showing the implementation. Ask which failure is most expensive to the buyer.

## 2:00–5:00 | SignalDesk revenue engagement

In SignalDesk-Acquisition-Intelligence:

```bash
python -m app.salesforce.demo
python -m pytest -q tests/test_salesforce_contract.py tests/test_salesforce_reader.py tests/test_salesforce_reliability.py
```

Expected offline fixture: 7 records, 2 review-required, 3 blocked, 2 held.
Show the reason a record is held or blocked. Review-required does not mean
qualified, approved or authorized for outreach.

Explain the reader's fixed GET, query cap, no redirects, no retries and sanitized
output. Point to tests for missing fields, inconsistent counts and failed access.

**Recorded live evidence:** on November 8, 2026, the operator completed a
Developer Edition read with 2 synthetic Leads: 1 blocked, 1 review-required,
0 held. Lead metadata reported query allowed and create/update/delete denied.
See [provenance and limitations](SALESFORCE_DEV_ORG_VALIDATION.md). This walkthrough
remains offline; showing recorded evidence is not a new live run.
Agentforce, CRM writes and delivery are separate, unimplemented integration gates.

## 5:00–9:00 | AEGIS-NHI risk engagement

In AEGIS-NHI:

```bash
python -m aegis_nhi.cyber_graph --scenario data/scenarios/shadow_ai.json --output artifacts/shadow_graph.json
python -m aegis_nhi.cyber_graph --scenario data/scenarios/shadow_ai.json --verify artifacts/shadow_graph.json
python -m aegis_nhi.source_contract data/cross_source/two_source_demo.json --source fictional-iam --source fictional-audit
python -m pytest -q tests/test_source_contract.py tests/test_cyber_graph.py
```

First show the existing single-case graph and verification against its selected
source. Then show the **separate** ingestion-contract report: 2 observations and
1 explicitly declared event link.

Explain three rejection cases using the acceptance tests:
- Institution or case mismatch rejects the whole bundle.
- Contradictory action/outcome rejects the proposed association.
- Missing evidence from either endpoint rejects the link.

With no explicit links, matching labels remain separate records. The report says
NOT_AUTHORIZED_FOR_ACTION and DECLARED_NOT_AUTHENTICATED.

**Boundary:** the ingestion contract does not feed the case graph yet. Source
adapters, source authentication and an integrated analyst interface remain future
work. Hashes provide consistency checks, not proof that a source is truthful.

## 9:00–11:00 | Explain the commercial choice

Open the [Studio worksheet](TAGM_CLIENT_TO_VALUE_STUDIO.md). Show the downside
before the base case. State that all values are illustrative assumptions.

Compare extending existing CRM/security tools with a bounded custom component.
Separate released staff capacity from realized cash savings. Do not use fixture
counts as client outcomes or combine speculative avoided loss with labor value.

Ask: "Which baseline, operating cost or adoption assumption would most change
your decision?"

## 11:00–12:00 | Request a concrete next gate

Revenue: review the completed limited live milestone, then authorize remaining
negative-case tests and define pilot baselines, ownership and acceptance thresholds.

Risk: select one real source schema for an offline adapter design, identify its
owner and establish the institution/case mapping before any cross-source pilot.

Record: sponsor decision, evidence shown, outstanding uncertainty, owner, next
gate and date. No claim of completed deployment or customer ROI follows from
this demonstration.

## Presenter checklist

- Record the exact commit and commands used; confirm CI for that revision.
- Keep credentials and customer data out of the demonstration.
- If a demo fails, show the failure, retain the result and explain the next check.
- Do not present prepared screenshots as a live run.
- End with the business decision and its evidence, not a feature inventory.
