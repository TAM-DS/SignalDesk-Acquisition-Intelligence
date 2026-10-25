# Validation record — v0.4.0 release candidate

October 24, 2026. This is the v0.4 release-candidate status, not a final release acceptance certificate.

## Evidence presently available
- Developer-reported local run: **108 automated tests passing** in the Mac development environment prior to the release-readiness changes. The new GitHub Actions matrix and installed-wheel smoke test were subsequently added; their outcomes must be checked independently.
- Live Acquisition Intelligence: the developer observed a successful OpenAI-powered company-discovery session displaying candidate companies, citations, and an opt-in Save for Human Review control. A later browser screenshot confirmed that Aera Technology was saved to a **pending** persistent review item with five reference links.
- The screenshot confirms queue persistence/display, **not** approval, accepted buyer-fit claims, successful SDR lead creation, or completed end-to-end handoff.
- The dashboard and delivery screenshots do not establish real email delivery. Sending remains simulated by design.
- The MIT LICENSE, version metadata, README and wheel packaging were updated as release preparation. The installed-wheel test must pass before we claim a distributable build is validated.

## October 25 — observed end-to-end browser acceptance

Developer-provided screenshots document this specific sequence:

1. Live Acquisition Intelligence returned JPMorgan Chase & Co. as a **candidate**, with provider-linked sources and explicit unverified-evidence warnings; candidate was saved to the human review queue.
2. The review interface presented a form populated with contact/department, seller, offering, ICP, and an explicit authorization checkbox. The next screenshot establishes that transfer completed, but the form screenshot alone does not establish source truth or verified recipient identity.
3. The original SDR workspace displayed **JPMorgan Chase & Co.** with status **Needs evidence** and a decision-history `ACQUISITION_HANDOFF` event: "Human-reviewed candidate transferred; no research or outreach started."
4. A later developer screenshot displayed `LIVE_STARTED` and `LIVE_COMPLETED` after the user separately initiated live research in the SDR workspace (two response calls, one search call). The AI-assisted review did **not** confirm the named contact's role or employment. The system displayed an **Evidence hold** rather than an approvable outreach draft.
5. The `RESEARCH` decision-history entry documents a request for further evidence **without automatically starting another live request**. No email-provider connection or actual outgoing delivery exists.

**What this demonstrates:** an observed controlled research → human-authorized lead creation → evidence hold workflow. **What it does not demonstrate:** that JPMorgan is a buyer, that the named individual has the asserted role, that provider-returned sources prove every claim, or that messages were delivered.

The author also confirmed that the 108 local automated tests passed (`108 passed in 0.99s`) following the initial release-readiness updates. A later GitHub Actions matrix run passed on commit `d68b129`. A subsequent change restored `.env.*`, `*.sqlite`, and `*.sqlite3` ignore rules; the final merged SHA still requires green CI.

## Release acceptance not yet demonstrated
- [ ] GitHub Actions Python matrix passes on the final branch SHA.
- [ ] Built wheel installs in isolation and serves both SDR and Acquisition Intelligence assets.
- [x] Browser: observed human-authorized acquisition handoff to an SDR lead in Needs evidence, with no automatic outreach. Independent verification of company fit and contact identity is not claimed.
- [ ] Confirm browser rejection, existing-lead/duplicate, and Do Not Contact behavior (automated tests exist; prior screenshots were reported, not independently revalidated for this release).
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
