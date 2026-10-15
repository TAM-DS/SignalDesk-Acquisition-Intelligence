# Repository handoff

## Include

Commit the release source, tests, README, dependency files, and docs. The release archive contains only the updater's explicit source-file list. Keep live lead records, local backups, credentials, and private screenshots out of the repository. The existing ignore rules are a convenience, not a substitute for reviewing staged files.

Before a first commit, inspect `git status --short` and `git diff --cached`. Run `python -m pytest -q`. Use fictional fixture leads for a public demo and inspect screenshots for personal information before publishing them. Choose a license deliberately before describing the repository as open source.

## Demo sequence

1. Show source evidence and an evidence hold on the fictional leads.
2. Approve a draft, edit it, and demonstrate that approval is revoked.
3. Show Do Not Contact remaining active after refresh.
4. Explain the exact-version approval fingerprint and simulated delivery.
5. Discuss the observed live-run result and its remaining claim-mapping gap using VALIDATION.md.

## Acceptance boundary

This is a local prototype ready for a portfolio walkthrough after local installation checks. It is not a validated production sales system. No email delivery, CRM connection, authentication, tenant isolation, immutable audit archive, or measured sales lift is claimed.

The next quality milestone is a small labeled evaluation of draft factual support, fit decisions, and holds. Record the model, prompt version, source dates, latency, usage, and human judgments; compare with a simple baseline. Do not treat one successful draft as an accuracy benchmark.
