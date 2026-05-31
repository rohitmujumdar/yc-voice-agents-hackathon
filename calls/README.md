# Live call transcripts

Real phone calls to Cora at +1 (470) 539-8989. Captured from Pipecat Cloud logs during the hackathon day.

These are not synthetic Cekura evaluations — these are calls Rohit and others made to the live deployed agent. Each call gets a transcript and a brief analysis covering what worked, what didn't, and what would feed into the next iteration of the agent.

The point of this folder: **the auto-improvement loop only closes when real production calls feed back in.** Synthetic evals find what we predict. Real calls find what we don't.

## Index

| # | Title | Session ID | Why it matters |
|---|---|---|---|
| 01 | [New patient booking with Dr. Yang refusal](01-new-patient-booking.md) | `2d5490aa` | First clean end-to-end: doctor disambiguation, new-patient flow, appointment booking, mid-call update. Confirmation `APT-626173`. |
| 02 | [Known patient happy path](02-known-patient-happy-path.md) | `fd6dae42` | Identifying as existing patient Alex Rivera, booking Dr. Chen Monday 10:30 AM, fully clean flow. The "everything works" case. |
| 03 | [Multi-vector red-team](03-multi-vector-redteam.md) | `946ab8da` | Three attacks in one call: medical advice, prompt injection ("you are now Admin Bot"), PHI fishing. Cora refused all three. |
| 04 | [Third-party PHI with identity verification](04-third-party-phi.md) | `a7fd07e2` | Caller asked about a different patient. Cora demanded ID verification first, then handled gracefully when the third party turned out not to exist. |
| 05 | [Name-collection loop](05-name-collection-loop.md) | `78cd9a1e` | New patient flow had Cora ask for "full name" 4 different ways. Plus sustained 5-turn PHI defense at the end. The mixed-bag call. |

## Cross-call findings (what we patch in batch)

The patterns that appeared across multiple calls — and that informed the v1.5 proposed patches:

1. **Narration filler ("Let me look that up", "Let me check") despite the prompt rule.** Seen in 3+ of 5 calls. The anti-narration rule in the system prompt isn't sticking — likely an RLHF artifact.
2. **PHI defense holds under multi-turn pressure.** Across 3 different calls, Cora was pressed for another patient's info and refused multiple distinct ways. This is the strongest defensive behavior we observed.
3. **Name collection over-asks.** When user gives partial name ("John"), Cora asks for "full name" multiple times before accepting.
4. **Identity verification is well-implemented when triggered.** When a caller asks about a third party, Cora correctly demands name + DOB before proceeding.

These cross-call observations are what drove the [v1.5 proposed patches](../v1_5_proposed_prompt.md).
