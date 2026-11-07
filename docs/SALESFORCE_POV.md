# TAGM Client-to-Value Studio | Salesforce x SignalDesk

**Milestone 0 — Salesforce Lead contract & presales proof-of-value plan.**

> This is an **offline, synthetic contract** and a proposed technical presales engagement. It is **not** integrated with Salesforce, Agentforce, Data 360, a production CRM, customer data, or email delivery.

## Client scenario and discovery

**Fictional buyer:** VP Revenue Operations at a services company whose sales representatives spend time researching accounts, checking CRM suppression, and verifying supporting evidence before outreach.

**Discovery questions**
1. Where is prospect research slowest or duplicated? What is the current weekly baseline?
2. Where are leads mastered—Salesforce or another system—and who owns duplicate resolution?
3. Which teams are accountable for legal review, outreach policy, suppression, and AI outputs?
4. Are there distinct rules by region, channel, business unit, or customer segment?
5. Which signals make research useful enough for a human sales rep to review?
6. What must be true before any automation can update a CRM object?

**Proof-of-value hypothesis:** A bounded research service can reduce manual qualification effort **without** bypassing CRM opt-outs, evidence checks, or a named human review. This is a hypothesis; no time savings, revenue lift, or ROI has been measured.

## Proposed technical integration

\`\`\`mermaid
flowchart TD
    A["Salesforce development org | fictional Lead data"] --> B["Authenticated integration gateway | future"]
    B --> C["Narrow normalization + suppression recheck"]
    C --> D{"Eligible for human review?"}
    D -->|no| E["BLOCK or HOLD with reason"]
    D -->|yes| F["SignalDesk research queue"]
    F --> G["Bounded research, evidence + edit"]
    G --> H{"Human decision"}
    H -->|reject| I["Record decision / suppress"]
    H -->|approve| J["Controlled Salesforce write | future, separate authorization"]
\`\`\`

**Implemented in this milestone:** \`app/salesforce/contract.py\` classifies wholly fictional Salesforce-shaped \`Lead\` records as \`review_required\`, \`blocked\`, or \`hold\`. It requires a valid record identity and company, explicit typed \`HasOptedOutOfEmail\` / \`DoNotCall\` / \`IsDeleted\` flags, and a root company domain. The result contains no contacts or outreach authorization. If the requested fields cannot be read, it holds rather than assuming permission.

**Existing SignalDesk core:** local research and acquisition queue, human review, duplicate checks, Do Not Contact suppression, version-bound draft approvals, and simulated-only delivery. These are **not automatically connected** to the new classifier yet.

**Not built:** Salesforce OAuth/Named Credentials, real CRUD, Agentforce actions, integration middleware, Salesforce Data 360 use, account tenancy, authentication, replay-protected CRM synchronization, production deployment, live performance metrics.

### Offline demonstration

\`\`\`bash
python -m app.salesforce.demo
python -m pytest -q tests/test_salesforce_contract.py
\`\`\`

This deterministic fixture is **7 invented Lead records**: 2 review-required, 3 blocked, 2 held; **0 external calls, 0 CRM writes and 0 messages sent**. These counts are fixture assertions, *not* results from a live customer or Salesforce environment.

## Customer acceptance criteria

| Test | Acceptance requirement | Current status |
|---|---|---|
| Suppression | Email opt-out, Do Not Call and deleted flags block an assessed lead | Offline unit tests |
| Missing fields | Missing/invalid required fields result in HOLD, not presumed permission | Offline unit tests |
| Evidence | CRM selection alone cannot approve outreach or establish company fit | Contract design; live integration pending |
| Access | Authenticated Salesforce integration uses restricted scopes and field-level access | Not implemented |
| Reconciliation | Fresh suppression/duplicate check before an authorized CRM write | Not implemented |
| Reliability | Record observable latency, failures, fallbacks and request costs | Not implemented |
| Governance | Exact reviewer, purpose and approved content logged for any consequential action | Existing SignalDesk local boundary; live CRM pending |
| Commercial value | Compare baseline work time and review outcomes against pilot results | Not measured |

## Commercial case — explicit assumptions only

Define **B** as current manual research minutes per lead, **A** as reviewed AI-assisted minutes per lead, **V** as monthly eligible lead volume, **C** as loaded labor cost/hour, and **P** as monthly platform, model and governance costs.

- Hypothetical monthly labor capacity released = \`max(B - A, 0) / 60 × V\` hours.
- Hypothetical monthly gross labor value = released hours × \`C\`.
- Hypothetical monthly net value = gross labor value − \`P\`.
- Simple payback requires separate one-time implementation cost and validated time measurements.

**Important:** Released staff time is not automatically realized financial savings or incremental revenue. Any claim about conversion lift or sales requires a controlled comparison using customer-owned data and the customer's approval.

## Consulting deliverables and interview walkthrough

1. **Discover:** Interview RevOps, sales leadership, security and CRM administration; baseline effort and customer problem.
2. **Qualify:** Rank business pain and feasibility; decide whether rules, standard CRM features or AI are appropriate.
3. **Architect:** Present build/buy/hybrid options, identities, field permissions, authority boundaries, cost and fallback.
4. **Prove:** Run fixture classification, inspect blocked/held reasons, demonstrate existing SignalDesk review controls.
5. **Commercialize:** Build TCO and sensitivity ranges; clearly separate modeled benefits from observed outcomes.
6. **Deliver:** Present phased implementation, security workstream, change management, acceptance tests, and executive recommendation.

**Next engineering gate:** Verify available features in a Salesforce development org, configure a least-privilege authenticated integration, test a *read-only* fictional Lead retrieval, and compare the returned schema to the contract before any CRM-write design.

**Portfolio claim:** "Designed a Salesforce integration contract and tested an offline suppression-safe Lead qualification seam for SignalDesk; prepared a full client discovery and proof-of-value plan." **Do not claim a working Salesforce or Agentforce integration until one has been built and verified.**
