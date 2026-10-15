# SignalDesk product brief

## User and buyer hypothesis

Small B2B consultancies and technical-services firms doing founder-led sales. The user reviews individual opportunities; the buyer wants less research and rewriting without sacrificing credibility. This customer hypothesis is not yet validated.

## Problem

Drafting a plausible email is easy; checking whether the contact, business need, and claims are supported takes time. A queue of weak drafts can increase that burden. The product should make relevance and uncertainty visible before a message is approved.

## First workflow

Known lead → explicit fit criteria → business evidence → bounded draft → quality checks → human decision → simulation.

Approval is an application-state transition, not a model instruction. Do Not Contact takes precedence over business fit. Missing or contradictory context is a valid reason to stop.

## Product decisions

| Decision | Reason | Trade-off |
| --- | --- | --- |
| Known leads first | Establish contact context without buying a lead database | No bulk discovery |
| Business context only | Keep outreach relevant and professional | Less personal flattery |
| Source panel beside the draft | Reduce effort to verify claims | More screen space |
| Fixed workflow before agent loops | Make transitions testable | Less autonomous exploration |
| Approve one exact version | Avoid post-approval changes reaching delivery | Edits require another review |
| Suppression has priority | Respect a human rejection of contact | Some potentially qualified leads remain blocked |
| Separate fictional and live leads | Keep deterministic demos while testing real evidence | Live quality requires a separate evaluation |

## Evaluation plan

Use a fixed held-out lead set with human-reviewed evidence, including ambiguous identities, out-of-profile accounts, unknown pain points, stale and contradictory sources, and disallowed personalization. Compare manual work, a single-prompt baseline, and the proposed workflow on the same inputs.

Measure time per accepted draft including review, unsupported claim rate, identity errors, factual edit rate, rejection reasons, and total cost per accepted draft. Later measure qualified conversations without treating replies alone as success. Define acceptance thresholds with the pilot customer before evaluation. No 90% automation or revenue lift is claimed.

## Commercial experiment

Interview three founder-led sellers; observe how they currently research and review outreach. Seek a pilot commitment and test willingness to pay for a workspace subscription with bounded research usage. Include support, infrastructure, model/search, and customer review costs. Do not infer willingness to pay from enthusiasm about a demo.

## Honest portfolio description today

Built a local SDR review prototype with bounded OpenAI web research and structured drafting, source-linked review, human approval, edit-triggered approval revocation, contact suppression, persisted decision history, and simulated delivery. Provider integration has been tested with mocks; live quality and commercial outcomes remain to be measured. Production email integrations are planned.
