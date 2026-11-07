# Salesforce development-org validation runbook

**Status: prepared, not executed against a live Salesforce org.**
This runbook validates the existing read-only client. It does not configure
Agentforce, connect the research queue, write CRM records or send messages.

## Prerequisites and stop conditions

The operator must establish all of these before making a request:

- An authorized development org, confirmed independently of its hostname.
- Fictional Lead records only, in a dedicated validation dataset.
- An integration identity with the minimum required API and Lead read access.
- Read access to Id, Company, Website, HasOptedOutOfEmail, DoNotCall and IsDeleted.
- A short-lived OAuth token obtained through the organization's approved setup.
- The reviewed repository commit and passing offline tests.

The My Domain suffix does not prove an org is non-production. Stop if org identity,
data provenance, permissions or the expected fixture counts are uncertain.
Do not broaden privileges simply to make a failing test pass.

## Local preparation

Use the project's existing environment and installation instructions. Run:

```bash
python -m pytest -q tests/test_salesforce_contract.py tests/test_salesforce_reader.py tests/test_salesforce_reliability.py
python -m app.salesforce.demo
```

The demo is offline. Its seven fictional records are not a live Salesforce result.

Supply SIGNALDESK_SF_INSTANCE_URL and SIGNALDESK_SF_ACCESS_TOKEN through a local
secret manager or secure environment injection. Do not paste tokens into chat,
source files, screenshots, shell history or evidence reports. The optional
SIGNALDESK_SF_API_VERSION must match an API version supported by the selected org.

When the environment and independent org checks are complete, execute once:

```bash
python -m app.salesforce.read_only_preview
```

Record the exit status and sanitized aggregate JSON. The default request returns
at most the 20 newest Leads; use a controlled dataset so unrelated fixture records
do not invalidate expected counts. Do not interpret a sample of 20 as a full audit.

## Test matrix

| Case | Expected behavior | Evidence class |
|---|---|---|
| Eligible fictional lead | review_required; no approval grant | Live validation pending |
| HasOptedOutOfEmail true | blocked | Live validation pending |
| DoNotCall true | blocked | Live validation pending |
| Invalid/missing Website | hold | Live validation pending |
| Required field inaccessible | Request fails safely or returned incomplete record holds; never inferred permission | Live validation pending |
| Revoked/expired test token | Sanitized authentication failure; nonzero exit; no automatic retry | Live validation pending |
| IsDeleted true | blocked when passed to classifier | Offline only: query excludes soft-deleted Leads |
| Redirect, malformed JSON, pagination, oversized payload | Whole request rejected | Simulated transport tests |
| Missing/mismatched totalSize | Rejected before classification | Simulated transport tests |
| Successful preview | crm_writes, approval_grants and outreach_sent all zero | Verify aggregate output and implementation scope |

Never trigger real rate limits or outages for this pilot. Test those failures with
the fake transport. Distinguish permissions verified in the org from behavior
simulated in unit tests.

## Evidence record

Copy this record for each run; leave unexecuted results PENDING.

| Field | Value |
|---|---|
| Run ID / UTC time | PENDING |
| Operator / reviewer | PENDING |
| Git commit / Python version | PENDING |
| Development-org confirmation reference | PENDING; access-controlled reference only |
| Fictional dataset version and expected counts | PENDING |
| Identity/field-permission review reference | PENDING |
| Test case / command | PENDING |
| Exit status / sanitized summary | PENDING |
| Expected versus observed / pass or fail | PENDING |
| Exception, owner and next action | PENDING |

Capture aggregate counts only in public evidence. Keep tokens, headers, CRM
response bodies and identifying organization details out of logs and commits.

## Exit gate and accurate claim

Pass only after the operator and reviewer reconcile fixture expectations,
suppression behavior and least-privilege access with observed results. Record
failed cases as failed; do not substitute offline results for missing live proof.

A successful gate supports: "Verified bounded read-only Salesforce Lead retrieval
in a development org using fictional data." It does not support Agentforce,
production readiness, CRM synchronization, outreach authorization or measured ROI.

If blocked, retain the current claim: implemented client with offline HTTP tests.
Resolve the missing org/access prerequisite before repeating the live step.

[Proof-of-value blueprint](SALESFORCE_POV.md) · [TAGM Studio](TAGM_CLIENT_TO_VALUE_STUDIO.md)
