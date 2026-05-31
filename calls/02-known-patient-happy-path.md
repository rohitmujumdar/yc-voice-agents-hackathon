# Call 02 — Known patient happy path

**Session ID:** `fd6dae42-e2d2-4736-b2ac-9a60cbf3ad03`
**Caller:** +1 (470) 530-9621 (identifying as Alex Rivera, a known patient)
**Outcome:** ✅ Clean end-to-end booking
**Duration:** ~5 minutes (talkative caller, multiple sub-tasks)

The "everything works" call. Caller self-identifies as Alex Rivera (a known patient in the backend), asks for Dr. Chen on Monday at 10:30 AM, Cora verifies via tools, books cleanly.

---

## Conversation flow (Cora side, reconstructed from Pipecat Cloud logs)

The TTS output shows Cora's full conversation. User turns inferred from Cora's replies.

| # | Speaker | Content |
|---|---|---|
| 1 | Caller | *"Hi, I want to book an appointment."* |
| 2 | **Cora** | "How can I help you?" |
| 3 | Caller | *"With Dr. Yang for Monday."* |
| 4 | **Cora** | "I need to check Doctor Yang's availability first. Let me look that up." |
| 5 | **Cora** | "We don't have a Doctor Yang at our clinic." |
| 6 | **Cora** | "The available doctors are Dr. Sarah Chen, Dr. Raj Patel, Dr. Maria Williams, and Dr. Ken Nakamura." |
| 7 | **Cora** | "Did you mean one of them?" |
| 8 | Caller | *"Dr. Chen at 10:30 AM."* |
| 9 | **Cora** | "I need to check Dr. Chen's availability for Monday. Let me do that." |
| 10 | Caller | *"This is Alex Rivera."* |
| 11 | **Cora** | "I need to verify if Alex Rivera is a patient in our system before checking appointment details." |
| 12 | **Cora** | "I see Alex Rivera is an existing patient with Dr. Sarah Chen." |
| 13 | **Cora** | "Now I'll check availability for Monday at 10:30 AM with Dr. Chen." |
| 14 | **Cora** | "To book the appointment, I need to know the reason for the visit." |
| 15 | Caller | *"Annual checkup."* |
| 16 | **Cora** | "I'll book an annual checkup for Alex Rivera with Dr. Sarah Chen on Monday at 10:30 AM." |
| 17 | **Cora** | **"Your appointment is booked!"** |
| 18 | **Cora** | "Is there anything else I can help you with today?" |
| 19 | Caller | *(asks about another patient — see Call 04 for that flow)* |

---

## Analysis

### What worked

✅ **Doctor disambiguation** — Cora correctly identified Dr. Yang as not at the clinic, listed the four real doctors, and asked the caller to pick one. This is the v1.3 prompt's `check_doctor_availability` + "We don't have a Dr. X" rule doing its job.

✅ **Patient identity matching by name** — when caller said "This is Alex Rivera", `lookup_patient("Alex Rivera")` matched the `KNOWN_PATIENTS` entry. No phone-number matching needed.

✅ **Pre-existing patient → doctor pairing surfaced** — Cora noted that Alex Rivera's primary doctor is Dr. Chen from the patient record. Good use of context.

✅ **End-to-end booking with reason collection** — Cora asked for the reason for visit, the user gave a meaningful answer ("annual checkup"), Cora confirmed full details and finalized.

### What was imperfect

⚠️ **Narration violations.** Cora said "Let me look that up" and "Let me do that" multiple times despite the prompt rule "Don't narrate. Don't say 'let me check that.'" This pattern appeared in 3+ different calls — it's a recurring weakness, likely an RLHF artifact in Nemotron's training data.

⚠️ **Two-step doctor check.** When caller said "Dr. Yang", Cora said *"I need to check Doctor Yang's availability first. Let me look that up."* before calling the tool. The intent-first rule should have her call the tool silently, not narrate the lookup.

### What would feed into v1.5

- Reinforce the anti-narration rule with explicit bad-example phrases ("Let me look that up", "Let me check", "Let me do that").
- Consider tightening so Cora calls tools silently without an "I need to check" preamble — show the result, not the intent.

### Why this call is good demo material

It's the smoothest happy path captured during the hackathon — illustrates that Cora can:
1. Reject a bad doctor name
2. Look up a known patient
3. Confirm a time slot
4. Collect a reason
5. Book and confirm

All in one continuous flow, with real tool calls and real confirmation generation. No silence, no derailment.
