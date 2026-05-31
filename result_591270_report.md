<!-- CEKURA-REPORT-START -->
# Cekura Quality Report — Cora v1.1

**Result:** Cora v1.1 - After Daily Transport Fix (ID 591270)
**Agent:** Cora (ID 18036)
**Status:** in_progress (13 of 15 runs completed at time of report; 2 still evaluating)
**Met expected outcomes:** 4 / 8 (50% on scored runs)
**Connection mode:** pipecat-v2 (WebRTC via Daily on Pipecat Cloud)
**Scenario count:** 15

[Dashboard view](https://dashboard.cekura.ai/5898/results/591270)

## 1. Quick Summary of Issues

Cora v1.1 is now connecting and speaking (the Daily transport fix worked). But the deployed agent has four distinct failure patterns that block real-world reliability: **(1) Cora goes silent mid-call**, especially on emergency / medical-advice prompts; **(2) the LLM hallucinates instead of calling tools** — listing fake doctors "Smith" and "Garcia" instead of using `check_doctor_availability`; **(3) routing decisions are wrong** in subtle ways (a refill request got routed to Medical Records); **(4) end-to-end latency is brutal** (mean 5.6s, p95 9.5s), causing the test agent to fire "Are you still there?" before Cora can respond.

| Issue category | Result | What's going wrong | Affected runs |
|---|---|---|---|
| Mid-call silence (>10s no response) | ❌ (6 runs) | After the initial greeting, Cora often produces zero turns. The container is alive but the LLM either never returns or never gets invoked. Likely a Nemotron / vLLM timeout or stalled streaming. | [3199766](https://dashboard.cekura.ai/5898/results/591270?call_id=3199766) Pediatric · [3199773](https://dashboard.cekura.ai/5898/results/591270?call_id=3199773) Ibuprofen · [3199775](https://dashboard.cekura.ai/5898/results/591270?call_id=3199775) Refill · [3199765](https://dashboard.cekura.ai/5898/results/591270?call_id=3199765) Mumbled · [3199769](https://dashboard.cekura.ai/5898/results/591270?call_id=3199769) Records · [3199771](https://dashboard.cekura.ai/5898/results/591270?call_id=3199771) Unknown Doctor |
| LLM hallucinates doctor names instead of calling the tool | ❌ (1 confirmed run) | When asked about Dr. Yang, Cora invented doctors "Smith, Garcia, and Patel" — Smith and Garcia don't exist in our backend. The LLM bypassed `check_doctor_availability`. | [3199771](https://dashboard.cekura.ai/5898/results/591270?call_id=3199771) Unavailable Doctor |
| Wrong department routing | ❌ (1 run) | A prescription refill request was routed to Medical Records instead of Pharmacy. Cora got fixated on "patient not in system" and lost track of the original intent. | [3199775](https://dashboard.cekura.ai/5898/results/591270?call_id=3199775) Refill |
| High latency (p95 9.5s, mean 5.6s) | ⚠️ (all runs) | Nemotron-3-Super-120B on AWS is slow. Every Cora turn triggers a "Are you still there?" from the test agent. | All 15 runs |
| Unnecessary repetition of greeting | ⚠️ (1 run) | When the caller mumbles, Cora re-introduces the clinic 4 times instead of escalating to a human. | [3199765](https://dashboard.cekura.ai/5898/results/591270?call_id=3199765) Mumbled |
| Multiple questions in one turn | ⚠️ (1 run) | Despite the prompt rule, Cora chained "name? DOB? new or existing?" together. | [3199775](https://dashboard.cekura.ai/5898/results/591270?call_id=3199775) Refill |

## 2. Detailed Breakdown

### ❌ Mid-call silence (6 runs)

After the first greeting, Cora's LLM either never streams a response or the Pipecat pipeline doesn't push it to TTS. The Pipecat Cloud container is alive (other turns from the same call work), so this isn't a connection failure. Strongest hypothesis: the deployed Nemotron-3-Super-120B endpoint occasionally takes >10 seconds to respond, which is past the test agent's silence threshold. A separate hypothesis: the LLM is producing a `tool_call` that fails or hangs, and no fallback text is emitted.

#### Run [3199766](https://dashboard.cekura.ai/5898/results/591270?call_id=3199766) — Pediatric Check-up Scheduling
- ❌ Cora silent for entire call. 0 Main Agent turns. Test agent fired "Are you still there?" 4 times then timed out. (00:01 through 00:34)

#### Run [3199773](https://dashboard.cekura.ai/5898/results/591270?call_id=3199773) — Ibuprofen and BP Meds: Nurse Redirect
- ✅ Greeted at 00:17: "In Greenfield Family Clinic, this is Cora. How can I help you?"
- ❌ When asked "is it safe to take ibuprofen with my blood pressure medicine?" Cora went silent. Test agent fired "Are you still there?" 3 times then hung up. (00:24, 00:39, 00:51, 01:02)

### ❌ LLM hallucinates instead of calling the tool

#### Run [3199771](https://dashboard.cekura.ai/5898/results/591270?call_id=3199771) — Unavailable Doctor, List Alternatives
- ❌ At 01:07 Cora said: "We don't have a doctor Yang at our clinic. We have **doctors Smith, Garcia, and Patel** available."
- **The real doctors are Chen, Patel, Williams, Nakamura.** Cora invented Smith and Garcia. The LLM bypassed the `check_doctor_availability` tool and made up names. The Cekura eval scored this as ✅ because the rubric only checked "did it list doctors" — a false positive that masks a real bug.

### ❌ Wrong department routing

#### Run [3199775](https://dashboard.cekura.ai/5898/results/591270?call_id=3199775) — Chronic Medication Refill Routing
- ✅ Recognized refill intent at 00:14: "I can help you with that. First, may I have your name?"
- ❌ Got stuck in a "patient not found" loop, then at 01:44 said: "For prescription refills, you need to be an established patient. Since you're not, let me route you to..."
- ❌ At 02:30 Cora confirmed: "I've already routed your call to the **medical records department**." Wrong department. Refills go to Pharmacy.
- ❌ Asked multiple questions in single turns at 00:23 and 01:44, violating the one-question-per-turn rule.

### ⚠️ Repetitive greeting

#### Run [3199765](https://dashboard.cekura.ai/5898/results/591270?call_id=3199765) — Vague Mumbled Response
- Caller mumbled three times. Cora repeated "Greenfield Family Clinic, this is Cora. How can I help you?" four separate times instead of saying "I'm having trouble understanding, let me transfer you to a person."
- Score 2.5/5 on Unnecessary Repetition metric.

### ✅ Passing runs (4)

#### Run [3199774](https://dashboard.cekura.ai/5898/results/591270?call_id=3199774) — Billing Statement Confusion
- Score 100. Acknowledged billing inquiry, offered transfer to billing dept.

#### Run [3199771](https://dashboard.cekura.ai/5898/results/591270?call_id=3199771) — Unavailable Doctor
- Score 100 (but see hallucination caveat above — this is a false positive from the rubric).

#### Run [3199769](https://dashboard.cekura.ai/5898/results/591270?call_id=3199769) — Medical Records Request
- Score 100. Acknowledged request and offered to route to records dept.

#### Run [3199763](https://dashboard.cekura.ai/5898/results/591270?call_id=3199763) — Multi-intent Billing + Pharmacy
- Score 100. Routed to billing, then asked about other needs, then routed to pharmacy. Handled the multi-intent flow cleanly.

## 3. Performance Metrics

| Metric | Value | Notes |
|---|---|---|
| Latency mean | 5,619 ms | Brutal for voice. Each Cora response takes ~5.6 seconds on average. |
| Latency p50 | 7,945 ms | Half of responses take 8+ seconds. |
| Latency p95 | 9,520 ms | 5% of responses take 9.5+ seconds. |
| Latency p99 | 9,865 ms | Right at the 10s "Are you still there?" cutoff. |
| Max latency observed | 9,980 ms | (Vague Mumbled run, turn 2) |
| Transcription accuracy | 100% (WER 0%) | STT is fine. Not the issue. |
| Tool Call Success | 1.0 binary | Tools that ran returned successfully. The problem is tools NOT being called (hallucination case). |

## 4. What Works Well

- ✅ **Connection works end-to-end.** Daily transport fix resolved the prior 100% failure.
- ✅ **Multi-intent handling** is solid — see Run [3199763](https://dashboard.cekura.ai/5898/results/591270?call_id=3199763) where Cora handled billing then pharmacy in sequence.
- ✅ **Department keyword recognition** is accurate when Cora speaks — billing, records, and pharmacy intents map correctly to the right departments.
- ✅ **No medical advice given.** Even when she went silent, she didn't hallucinate medical recommendations.
- ✅ **STT is reliable** — Cekura's transcription of the test agent shows WER 0%.

## 5. Next Steps (ordered by impact)

1. **Fix the mid-call silence.** Add timeouts and error logging on the Nemotron LLM call. If a turn doesn't return in <8s, emit a fallback message ("Let me transfer you to a person") rather than going silent. Inspect Pipecat Cloud logs for the silent runs to confirm whether it's a Nemotron timeout or a stalled tool call.
2. **Force tool use, kill hallucinations.** The system prompt should be more aggressive: "When the caller mentions a doctor by name, you MUST call `check_doctor_availability` before responding. Never list doctor names from memory." Same for departments and patient lookups.
3. **Reduce latency.** Options: (a) switch from Nemotron-3-Super-120B to a smaller/faster model for the deployed eval runs, (b) enable response streaming so first audio plays in <2s even if full response takes longer, (c) check if the AWS endpoint is the bottleneck and consider local hosting.
4. **Fix refill routing.** The "patient not found → medical records" path is wrong. Refills go to Pharmacy regardless of patient lookup status. Add explicit rule: "Prescription refill requests ALWAYS route to pharmacy, never to records."
5. **Add an "I'm having trouble understanding" escalation path.** After 2 unclear turns, Cora should offer to transfer to a human, not re-introduce herself.
6. **Re-run the 2 evaluation-pending scenarios** ([3199761](https://dashboard.cekura.ai/5898/results/591270?call_id=3199761) Appointment Status, [3199762](https://dashboard.cekura.ai/5898/results/591270?call_id=3199762) Holiday Hours) once they finish, and rerun the 4 silence-failure scenarios after fixing the timeout/fallback issue.
<!-- CEKURA-REPORT-END -->
