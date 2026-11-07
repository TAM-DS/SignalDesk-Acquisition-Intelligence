# TAGM Client-to-Value Studio

**Tracy Manning**  
**Enterprise AI Solutions Architect | Technical Pre-Sales | Forward-Deployed AI & Strategy**

Two reference engagements connect customer discovery to architecture, engineering
evidence, commercial reasoning and delivery decisions. This is a consulting
portfolio package hosted alongside SignalDesk, not a separate deployed product,
a record of paid client outcomes, or an integrated multi-system platform.

## Engagements

| Engagement | Buyer problem | Working evidence | Next gate |
|---|---|---|---|
| [Salesforce × SignalDesk](SALESFORCE_POV.md) | Qualification work must respect suppression and human authority | Offline Lead contract; bounded GET-only REST client; test/package matrix | [Development-org validation](SALESFORCE_DEV_ORG_VALIDATION.md) |
| [AEGIS-NHI](https://github.com/TAM-DS/AEGIS-NHI/blob/main/docs/CLIENT_ENGAGEMENT.md) | Risk decisions need traceable identity, action, grant and evidence relationships | Synthetic case graphs, policy replay and source-consistency verification | Authorized ingestion contract and explicit join validation |

## The engagement method

| Stage | Deliverable | Decision / exit condition |
|---|---|---|
| Discover | Workflow, sponsor, stakeholders, baseline and problem statement | Buyer confirms a meaningful problem and owner |
| Qualify | Feasibility, access, constraints, cost of inaction and stop conditions | Access and measurement are viable |
| Design | Build/buy/extend options, trust boundaries and failure modes | Sponsor selects an option with explicit trade-offs |
| Prove | Bounded demo, negative tests, evidence register and acceptance results | Observed results meet agreed criteria |
| Commercialize | TCO, sensitivity, capacity value and payback assumptions | Business case survives a realistic downside |
| Deliver | Phases, responsibilities, adoption, support and handover | Accountable owners accept the operating model |
| Present | Executive recommendation, remaining uncertainty and next decision | Named decision maker accepts, changes or stops scope |

## Revenue engagement — architecture decision

**Starting recommendation:** assess existing CRM features first, then use the
bounded custom reader only where an evidence-backed qualification workflow adds
value. The reader is separate from the local research queue today.

| Option | Advantage | Cost / limitation |
|---|---|---|
| Extend existing CRM workflow | Fewer moving parts, familiar administration | Confirm whether required evidence and review controls can be represented |
| Custom bounded SignalDesk adapter | Explicit suppression behavior and inspectable tests | Own schema changes, authentication, failure handling and support |
| Broader agent platform | Potential reusable workflow capabilities | Requires separate validation, licensing and authority design |

Deterministic suppression rules do not require an LLM. Agentforce is neither
implemented nor verified by this package. Discovery must establish whether an
agent adds value before selecting an agent platform.

## Risk engagement — architecture decision

Start with one synthetic investigation and prove the evidence relationships.
Evaluate existing SIEM/SOAR/IAM capabilities before proposing new infrastructure.
A successful export verification establishes consistency with a selected source,
not truth of the underlying source or permission to remediate.

Cross-source ingestion must identify source system, institution, case, event,
schema version and evidence provenance. Joining similar identifiers without
explicit scope is not acceptable. External feeds remain future work.

## Commercial worksheet — illustrative USD assumptions

For either engagement:
- Capacity hours/month = max(baseline minutes − assisted minutes, 0) × volume / 60.
- Capacity value/month = hours × loaded hourly labor cost.
- Net modeled value/month = capacity value − recurring operating cost.
- Payback months = one-time implementation cost / positive net modeled value.

Include software licenses, model usage, integration support, infrastructure,
governance and ongoing evaluation in recurring cost. Include discovery, build,
security review, training and migration in implementation cost.

| Scenario | Baseline / assisted minutes | Items/month | Labor/hour | Recurring/month | Initial cost | Hours/month | Net modeled value/month | Payback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Downside | 12 / 9 | 500 | $60 | $3,000 | $15,000 | 25.00 | −$1,500 | None |
| Illustrative base | 12 / 5 | 1,000 | $75 | $2,000 | $15,000 | 116.67 | $6,750 | 2.22 months |
| Upside | 12 / 4 | 1,500 | $85 | $2,500 | $15,000 | 200.00 | $14,500 | 1.03 months |

These figures are invented, not forecasts or achieved returns. Released time is
not automatically cash savings. If assisted work takes longer, record the extra
effort as an operating cost rather than hiding it behind the zero floor.
Do not add revenue uplift or avoided cyber losses without separate evidence.

## Pilot measurement plan

Before a pilot, agree the sample, exclusions, volume, time window and acceptance
thresholds. Compare similar manual and assisted tasks; include failed runs,
review time, corrections and escalations. Report sample size and limitations.

| Measure | SignalDesk | AEGIS-NHI |
|---|---|---|
| Effort | Minutes per reviewed lead | Minutes per reviewed investigation |
| Quality | Reviewer acceptance and correction rate | Correct evidence links and reviewer corrections |
| Control failure | Suppressed item incorrectly advanced | Wrong source join or unsupported action recommendation |
| Reliability | Failure rate, latency and bounded request counts | Reproduction failures, source mismatches and processing time |
| Adoption | Reviewer completion and reasons for rejection | Analyst completion and usability feedback |
| Economics | Actual operating cost versus modeled capacity | Actual operating cost; separately labeled risk assumptions |

Set numeric targets with the buyer; no invented acceptance threshold is presented
as a customer requirement. Any authority or suppression bypass blocks expansion.

## Proposed four-phase delivery

1. **Discovery:** sponsor, workflow, baseline, source ownership and scope.
2. **Proof:** synthetic demonstration, negative tests and architecture decision.
3. **Pilot:** only after authorized connectivity, permissions and evidence gates.
4. **Handover:** runbook, support owner, monitoring, review cadence and rollback.

The schedule is a proposal to estimate after discovery, not a promised deployment
date. Rollback means disabling the integration and returning to the established
manual workflow; it does not imply automatic reversal of external actions.

## Accountability

| Decision | Accountable | Responsible | Consulted |
|---|---|---|---|
| Business objective and pilot go/no-go | Business sponsor | Engagement lead | Finance and users |
| Architecture and integration scope | Technical owner | Solutions architect | Security and platform teams |
| Data access and permissions | Data/system owner | Platform administrator | Security and privacy |
| Consequential recommendation | Named business/risk reviewer | Assigned reviewer | Domain specialists |
| Operating handover | Service owner | Delivery team | Support and users |

These are proposed roles to assign to named people during discovery.

## Executive readout — six-slide outline

1. **Decision:** the workflow problem, sponsor and requested next gate.
2. **Options:** extend, buy or build; explain the selected trade-off.
3. **Evidence:** demonstrate the happy path and the most consequential failure.
4. **Economics:** baseline, assumptions, downside, cost and payback limitations.
5. **Delivery:** owners, dependencies, adoption and stop conditions.
6. **Recommendation:** proceed, revise or stop; state exactly what remains unverified.

## Portfolio positioning and evidence

The headline above expresses the target role and delivery focus. It is not a
claim of having held a Salesforce or Agentforce job title. Present each project
through: pain point → decision → trade-off → control → evidence → business consequence.

**Current evidence boundary:** software and synthetic tests exist; live Salesforce
org validation, cross-source security integrations and customer ROI remain pending.
