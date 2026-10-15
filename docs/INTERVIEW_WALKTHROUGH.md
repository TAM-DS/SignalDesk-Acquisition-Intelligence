# Interview walkthrough

## Opening

“I designed this around a salesperson’s decision: is this person appropriate to contact, and can I defend the message? The synthetic fixtures demonstrate the control path deterministically; live leads use bounded web research and drafting.”

## Demonstrate judgment

- Compare Meridian’s message with the source. Explain that a fact about manual reporting does not prove an ROI claim.
- Show Cedarline’s conflicting role information. The product stops rather than guessing which person to contact.
- Approve Harborlane, edit it, and show approval revocation.
- Approve again, select Do Not Contact, and show that suppression takes precedence.
- Inspect decision history. It is an ordinary local database log, not an immutable compliance archive.

## Explain the implementation

FastAPI validates requests; SQLAlchemy persists current state and events. An approval fingerprint covers the exact content and evidence. Revision checks prevent stale decisions. Delivery is a simulation; there are no email-provider credentials or email-delivery calls.

## Discuss what remains

Distinguish the fictional demonstration leads from live research. Show a live research run only after configuring the API and reviewing its actual results; do not imply the mocks establish live accuracy. Explain why uncertain evidence results in a hold. Product validation, measured live quality, authentication, tenant isolation, migrations, durable background jobs, and controlled provider delivery remain work for subsequent milestones.

## Coding practice exercises

1. Add a rejection-reason filter and explain the API/UI trade-off.
2. Add a test showing changed evidence invalidates approval.
3. Implement a draft-version history view without losing prior content.
4. Add CSV import with duplicate detection and clear validation errors.
5. Explain how an email send timeout differs from a failed database transaction.

## Explain an observed failure and the response

An earlier generated draft implied that the seller already served commercial-vehicle dealers. That was not supplied experience. We restricted seller descriptions to proposed capabilities and kept human approval mandatory. A subsequent user-operated live example avoided that assertion; this is a useful example, not a measured hallucination rate.

That same run exposed incomplete claim mapping: the message mentioned parts/service operations, but the claim list emphasized qualification facts instead. v0.3.1 tightens the prompt to map facts in the actual message. The backend checks source-ID membership, not factual entailment or complete coverage. A labeled evaluation is needed to measure improvement.

A concise portfolio description: “Built a local SDR research and review prototype with bounded OpenAI research, source references, version-bound human approval, persistent Do Not Contact controls, and simulated delivery.”
