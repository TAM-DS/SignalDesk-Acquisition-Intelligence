# Validation record — v0.4.0 release candidate

October 24, 2026. This is the v0.4 release-candidate status, not a final release acceptance certificate.

## Evidence presently available
- Developer-reported local run: **108 automated tests passing** in the Mac development environment prior to the release-readiness changes. The new GitHub Actions matrix and installed-wheel smoke test were subsequently added; their outcomes must be checked independently.
- Live Acquisition Intelligence: the developer observed a successful OpenAI-powered company-discovery session displaying candidate companies, citations, and an opt-in Save for Human Review control. A later browser screenshot confirmed that Aera Technology was saved to a **pending** persistent review item with five reference links.
- The screenshot confirms queue persistence/display, **not** approval, accepted buyer-fit claims, successful SDR lead creation, or completed end-to-end handoff.
- The dashboard and delivery screenshots do not establish real email delivery. Sending remains simulated by design.
- The MIT LICENSE, version metadata, README and wheel packaging were updated as release preparation. The installed-wheel test must pass before we claim a distributable build is validated.

## Release acceptance not yet demonstrated
- [ ] GitHub Actions Python matrix passes on the final branch SHA.
- [ ] Built wheel installs in isolation and serves both SDR and Acquisition Intelligence assets.
- [ ] Browser: check actual source claims and company fit, approve review only with a justified basis, explicitly authorize handoff, and confirm SDR lead status `research_needed`, without sending a message.
- [ ] Confirm browser rejection, existing-lead/duplicate, and Do Not Contact behavior.
- [ ] Confirm packaging and README links, review PR diff, and merge only after checks pass.

## Limitations
Provider-returned URLs are attribution/provenance, not evidence that quoted claims are true. Live API use requires explicit opt-in and may incur fees. This single-user local app is not authenticated or suited to public hosting, sensitive records, or production delivery.

---

## Historical validation — v0.3.1

October 15, 2026. Automated checks ran on Linux, Python 3.12.

## Automated checks

- 40 API/provider-contract tests passed in 7.17 seconds with temporary SQLite databases and mocked provider responses.
- Controls cover exact-version approval, edit invalidation, stale revisions, suppression, repeated simulations, evidence holds, content flags, cross-origin writes, persistence, API consent, domain validation, source-ID validation, run caps, provider failures, restart recovery, and suppression during in-flight research.
- JavaScript passed Node syntax checking.
- Upgrade smoke check preserved a SQLite Do Not Contact sentinel, environment file, and virtual-environment sentinel; database backup creation was confirmed.

## User-operated live observation

The user supplied v0.3 screenshots from October 15, 2026, following a Mac installation. One Rush Enterprises research run completed from approximately 08:47:33 to 08:48:00 America/Chicago. The UI recorded two response calls, 12,557 input tokens, 2,885 output tokens, one search call, and seven source references. The resulting draft remained in Needs review and did not visibly assert invented seller experience. Source cards showed neutral verification reminders and the fit label read AI-assisted. The user separately confirmed saved edits survived refresh and Do Not Contact persisted.

The draft's parts/service statement was missing from the claim-reference list. Qualification facts appeared in that list instead. A source titled Corporate Responsibility Report—2023 also showed why publication date and applicability require review. Source contents were not independently verified during this documentation work. These observations establish a completed run, not a factual accuracy rate or sales outcome.

## Remaining limits

v0.3.1 strengthens claim-mapping instructions and fixes the footer version. The new prompt has not been live-evaluated; no paid API calls were made during this update. Source-ID validation does not establish factual entailment or complete claim coverage. Existing saved drafts are not rewritten by installation.

Browser screenshots document v0.3, not an interactive v0.3.1 Mac check. After updating, confirm the v0.3.1 footer, saved draft, and persistent suppression locally. PostgreSQL, multiple workers, hosted security, real email delivery, and commercial outcomes remain unvalidated. Email delivery is absent by design.

Dependency versions are in requirements-tested.txt. Automated checks and this observed example do not establish production readiness.
