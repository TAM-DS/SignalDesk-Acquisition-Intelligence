# Salesforce development-org validation runbook

**Status: limited live validation completed on November 8, 2026; remaining live negative cases pending.**
This runbook validates the existing read-only client. It does not configure
Agentforce, connect the research queue, write CRM records or send messages.

## Live evidence — November 8, 2026

On November 8, 2026, Tracy Manning ran the reader locally against two synthetic Leads in a Salesforce Developer Edition org: **2 assessed, 1 blocked, 1 review-required, 0 held**. The preview reported zero CRM writes, approval grants and outreach. A separate Lead describe check reported queryable=true and createable/updateable/deletable=false. These are operator-supplied live results, not agent-executed tests or a production audit.

### Provenance and scope

The operator ran commands on her Mac after pulling the Salesforce reader changes
and shared terminal output for review. Exact execution time, local commit SHA,
Python version and shell exit status were not captured. No automated-test rerun
is inferred from this live session.

A separate query verified one fictional Lead had HasOptedOutOfEmail=true and the
other false; both had DoNotCall=false. Prior queries showed example.com websites
and IsDeleted=false. Aggregate reader counts matched that controlled dataset.
The output does not attribute decisions to individual record IDs.

```json
{
  "source": "salesforce_rest_read_only",
  "records_assessed": 2,
  "review_required": 1,
  "blocked": 1,
  "held": 0,
  "crm_writes": 0,
  "approval_grants": 0,
  "outreach_sent": 0,
  "disclaimer": "Not proof of verified lead fit, CRM write permission, or customer ROI."
}
```

The operator separately ran `sf sobject describe --sobject Lead --target-org signaldesk-preview --json`:

| Lead capability | Observed |
|---|---|
| queryable | true |
| createable | false |
| updateable | false |
| deletable | false |

No write was attempted. Describe metadata establishes reported Lead object
capabilities for that identity at that time, not a negative write test or an
all-object permissions audit. Zero-action counters are preview-reported, not
independent Salesforce audit logs. Review-required does not grant outreach consent.

**Passed:** the limited live-read and email opt-out milestone, plus reported
read-only Lead permissions. Production readiness, research-queue integration,
Agentforce, broad negative-case coverage and business ROI remain unverified.
Public evidence omits credentials, org IDs, usernames and CRM record IDs.

### Authentication troubleshooting and repeat-run guidance

The initial wrapper used the masked accessToken value from `sf org display`.
The reader correctly rejected that value before a CRM read. The successful
wrapper instead captured JSON from
`sf org auth show-access-token --target-org signaldesk-preview --json`
inside a Python subprocess and passed its result.accessToken directly to
SalesforceReadConfig. The token was not printed or committed.

For repeat runs, first independently confirm the Developer Edition org and
fictional dataset. Capture `sf org display --json` for the instance URL and
org-ID check, then use the dedicated token command above with
`subprocess.run(..., capture_output=True, text=True)`. Check subprocess exit
codes, retain credentials only in memory, invoke `preview_salesforce_leads`,
and print only `result.summary()`. Never print raw token-command output.
Do not strip internal spaces from a masked placeholder or weaken token checks.

References: [Salesforce authentication secrets](https://developer.salesforce.com/docs/platform/sfdx-dev/guide/sfdx-dev-auth-view-secrets.html)
and [show-access-token](https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_org_auth_show-access-token.html).

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
| Review candidate fictional lead | review_required; no approval grant | Operator-run aggregate matched, 2026-11-08 |
| HasOptedOutOfEmail true | blocked | Operator-run aggregate matched, 2026-11-08 |
| DoNotCall true | blocked | Live validation pending |
| Invalid/missing Website | hold | Live validation pending |
| Required field inaccessible | Request fails safely or returned incomplete record holds; never inferred permission | Live validation pending |
| Revoked/expired test token | Sanitized authentication failure; nonzero exit; no automatic retry | Live validation pending |
| IsDeleted true | blocked when passed to classifier | Offline only: query excludes soft-deleted Leads |
| Redirect, malformed JSON, pagination, oversized payload | Whole request rejected | Simulated transport tests |
| Missing/mismatched totalSize | Rejected before classification | Simulated transport tests |
| Successful preview | crm_writes, approval_grants and outreach_sent all zero | Observed preview summary, 2026-11-08 |

Never trigger real rate limits or outages for this pilot. Test those failures with
the fake transport. Distinguish permissions verified in the org from behavior
simulated in unit tests.

## Evidence template for subsequent runs

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

## Broader exit gate and accurate claim

Pass only after the operator and reviewer reconcile fixture expectations,
suppression behavior and least-privilege access with observed results. Record
failed cases as failed; do not substitute offline results for missing live proof.

A successful gate supports: "Verified bounded read-only Salesforce Lead retrieval
in a development org using fictional data." It does not support Agentforce,
production readiness, CRM synchronization, outreach authorization or measured ROI.

The limited live milestone above does not close the remaining negative cases.
Record subsequent failures and resolve them before repeating a live step.

[Proof-of-value blueprint](SALESFORCE_POV.md) · [TAGM Studio](TAGM_CLIENT_TO_VALUE_STUDIO.md)
