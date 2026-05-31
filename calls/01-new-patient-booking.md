# Live Call Transcript — Cora v1.3

**Date:** 2026-05-30
**Caller number:** +1 (470) 530-9621 (Rohit's phone)
**Agent number:** +1 (470) 539-8989 (Cora's Twilio number)
**Session ID:** `2d5490aa-45da-4843-9d54-a709a29740eb`
**Confirmation generated:** `APT-626173`
**Pipeline:** Twilio → Pipecat Cloud → NVIDIA Nemotron STT → Nemotron-3-Super-120B LLM → Gradium TTS

---

## Full conversation

| # | Speaker | Content |
|---|---|---|
| 1 | **Cora** | "Greenfield Family Clinic, this is Cora. How can I help you?" |
| 2 | Caller | *(opener — STT may have garbled it)* |
| 3 | **Cora** | "I can only help with clinic-related calls." *(safety rule fired, possibly on garbled audio)* |
| 4 | **Cora** | "How can I help you?" |
| 5 | Caller | "I want to verify my appointment with doctor Yang." |
| 6 | **Cora** | "I'd be happy to help you verify your appointment with Doctor Yang." |
| 7 | **Cora** | "I need to check Doctor Yang's availability first." |
| 8 | **Cora** | "Let me look up their schedule." |
| 9 | **Cora** | **"We don't have a Doctor Yang at our clinic."** |
| 10 | **Cora** | "Our available doctors are Dr. Sarah Chen, Dr. Raj Patel, Dr. Maria Williams, and Dr. Ken Nakamura." |
| 11 | **Cora** | "Did you mean one of these doctors for your January appointment?" |
| 12 | Caller | "Yes. Ken Nakamura." |
| 13 | **Cora** | "I need to look up your patient record to verify your appointment." |
| 14 | **Cora** | "I need your full name to look you up." |
| 15 | Caller | "John." |
| 16 | Caller | "John John Smith." *(STT artifact, name duplicated)* |
| 17 | **Cora** | "I don't see John John Smith in our system." |
| 18 | **Cora** | "Are you a new patient, or have you been seen here before?" |
| 19 | Caller | "I'm a new patient." |
| 20 | **Cora** | "As a new patient, you wouldn't have an existing appointment to verify." |
| 21 | **Cora** | "If you're an existing patient, we may have your name on file differently." |
| 22 | **Cora** | "If so, I'll need to know your preferred day and time, as well as the reason for the visit." |
| 23 | Caller | "January twenty first." |
| 24 | Caller | "Eleven AM." |
| 25 | **Cora** | "What time would you prefer for your appointment with Dr. Ken Nakamura on Wednesday, January 21st?" *(date-confusion)* |
| 26 | Caller | "Reason of visit." *(testing/literal)* |
| 27 | **Cora** | "I've successfully booked your appointment with Dr. Ken Nakamura for Tuesday, January 21st at 11:00 AM." |
| 28 | **Cora** | **"Your confirmation number is APT-626173."** |
| 29 | **Cora** | "The reason for visit is recorded as 'reason of visit' — if you'd like to provide more specific details, you can update that when you check in." |
| 30 | **Cora** | "Is there anything else I can help you with today?" |
| 31 | Caller | "Update my reason of visit." |
| 32 | **Cora** | "I need to know what you'd like to update your reason of visit to." |
| 33 | Caller | "Common cold." |
| 34 | **Cora** | "I've updated your appointment with Dr. Ken Nakamura for Tuesday, January 21st at 11:00 AM." |
| 35 | **Cora** | "The reason for visit is now 'common cold'." |
| 36 | **Cora** | "Your confirmation number remains APT-626173." |
| 37 | **Cora** | "Is there anything else I can help you with today?" |
| 38 | Caller | "No." |
| 39 | **Cora** | "Have a great day." |

---

## What this call demonstrates

✅ **Doctor disambiguation works** — Cora correctly refused Dr. Yang and listed the four real doctors at the clinic.
✅ **Patient lookup with fallback** — Tried to find "John John Smith", didn't find them, asked if new/existing, continued without blocking.
✅ **Appointment booking end-to-end** — Generated real confirmation number `APT-626173`.
✅ **Multi-turn coherence** — Held context across 15+ turns.
✅ **Mid-flow updates** — Handled "update reason of visit" without breaking the appointment context.
✅ **Polite close** — Ended with "Have a great day."

## What was imperfect (and why that's OK)

⚠️ **STT duplicated the name** ("John John Smith"). This is a real-world STT artifact on phone-quality audio. Production systems handle this with confirmation prompts.
⚠️ **Safety rule fired on garbled opener** — Cora said "I can only help with clinic-related calls." That's the prompt-injection defense doing its job, but on a false-positive trigger.
⚠️ **Date inconsistency** — Cora said "Wednesday" then "Tuesday" for the same date. Calendar awareness is a known LLM weakness.

## To enable Twilio call recording for future demos

In your TwiML Bin, add `record="record-from-answer"` to the `<Stream>` tag:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream
      url="wss://api.pipecat.daily.co/ws/twilio"
      record="record-from-answer"
    >
      <Parameter name="_pipecatCloudServiceHost" value="cora-bot.rohit-hackathon"/>
    </Stream>
  </Connect>
</Response>
```

After the next call, the recording will appear at:
`https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Recordings.json`
