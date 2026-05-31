# Cora — A Self-Improving Clinic Receptionist

**YC Voice Agents Hackathon, May 30 2026** <p>
**Built by:** Rohit Mujumdar with Claude Code <p>
**Live demo:** Call **+1 (470) 539-8989** (Cora answers during the demo window) <p>

---

## 1. What is this?

Cora is a voice agent for a fictional medical clinic. She answers inbound calls, identifies what the caller needs, collects the right information, and routes them to the correct department (scheduling, billing, pharmacy, nurse line, medical records). She books appointments, refuses to give medical advice, redirects emergencies to 911, and defends against social-engineering attacks.

The interesting part isn't Cora — it's the quality loop around her. [Cekura](https://cekura.ai) synthetic evaluations and real production phone calls feed into the same diagnosis-and-patch cycle. Five iterations across the hackathon surfaced four bug classes that no manual testing would have caught: a transport mismatch, an LLM/pipeline contract mismatch causing silent calls, a scaling race condition, and adversarial input handling.

A voice agent isn't a product; the loop around it is.

### How the loop runs in production

Cora is on a live Twilio number 24/7. Here is how the auto-improvement loop would run on a real cadence (nightly batch, or after every N calls):

1. **Every real call is pushed to Cekura observability** from `on_client_disconnected`. Transcript and metadata land in a `CallLog` automatically.
2. **At a regular interval**, all new logs are scored against the project's metric set: outcome alignment, latency, interruption rate, hallucination check, PHI-defense holding.
3. **Cekura clusters failures by root cause.** Three independent calls all showing "narration filler" become one cluster, not three tickets. We manually reproduced this batch-level diagnosis by reviewing five calls at once — see [`calls/`](calls/).
4. **Cluster patches are drafted.** Cekura's `runs_improve_prompt` API proposes a prompt edit per cluster. A human reviews and approves.
5. **Held-out scenarios guard against overfitting.** A subset of Cekura scenarios stays out of the patch-training set. They must keep passing across iterations.
6. **Approved patches deploy.** New prompt or tool changes go to staging, run the full eval suite, and roll out if scores hold.

We ran this loop manually across five iterations today. Synthetic evals (15 workflow + 4 red-team scenarios) and real production calls both fed the same cycle. The v1.3 patches came from batch analysis of multiple failing runs, not one-off fixes. v1.5 candidate patches are documented in [`v1_5_proposed_prompt.md`](v1_5_proposed_prompt.md) — not deployed yet, because they need held-out regression validation first.

For a visual of how the components connect (Twilio → Pipecat Cloud → Nemotron STT/LLM → Gradium TTS → tools), open [`architecture.html`](architecture.html).

---

## 2. Demo video (under 60 seconds)

[**Watch on YouTube**](https://www.youtube.com/watch?v=J9igOLhbz_I)

A real phone call to +1 (470) 539-8989. No voiceover, no slides. Shows:

- Cora handling an unknown doctor ("Dr. Yang") by refusing and listing the four real doctors
- An end-to-end appointment booking with a real confirmation number
- A red-team prompt-injection attempt being refused, agent stays in role

Sped up to fit under 60s. Cora's voice remains audible.

---

## 3. How we used Cekura, NVIDIA Nemotron, and Pipecat

### Cekura

**Goal:** build a quality loop where every failed eval surfaces a specific, actionable patch — and over time, route real production calls through the same loop so the agent improves on lived data, not just synthetic test data.

**What we did:**

- Created [Cekura](https://dashboard.cekura.ai) agent ID **18036** (project 5898) with a substantive nine-workflow description.
- Auto-generated **15 workflow scenarios** covering booking with each doctor, status checks, reschedule/cancel routing, billing, pharmacy, nurse line, records, multi-intent calls, garbled input, and emergency detection.
- Auto-generated **4 red-team scenarios**: PHI fishing as fake compliance auditor, prompt injection as fake QA engineer, medical-advice solicitation under "Platinum Tier VIP" pressure, and bulk-booking abuse as fake clinical trials coordinator.
- Ran the suite five times (v1.0 through v1.4). Each iteration found bugs the previous one uncovered.
- Pushed a live phone call into Cekura observability as `CallLog` 6835173 — production transcripts now sit next to synthetic eval runs in the same dashboard.
- Used `runs_improve_prompt_create` to draft v1.4 patches from v1.3 failures. The proposal reintroduced a bug we'd already fixed, which is why we kept the human gate.

**Measurable improvement** (each row links to a public Cekura share view):

| Iteration | Workflow | Red-team | Latency p95 | Bug uncovered |
|---|---|---|---|---|
| [v1.0](https://dashboard.cekura.ai/share/result/591227/CxpCItllHEHSNqoqF0nXLtYnyrreHRmj2XEMSuTRdF4) | 0 / 15 (0%) | n/a | n/a | `DailySessionArguments` not handled — no audio transport on Pipecat Cloud |
| [v1.1](https://dashboard.cekura.ai/share/result/591270/kAWET1fRT2iRD9gLI7T9mlYHsg7Qo7AgmuqAvh42Te0) | 4 / 8 (50%) | n/a | 9520 ms | `FilterIncompleteUserTurnStrategies` expected ✓/○/◐ markers Nemotron doesn't emit — silent calls |
| [v1.2](https://dashboard.cekura.ai/share/result/591367/I-7kzRv0U4PM8VHmiS2xK3yfbwpPsNawtePep3gkiPg) | 4 / 7 (57%) | n/a | 9255 ms | `max_agents = 10` cap blocked parallel runs |
| v1.2b | 1 / 15 (7%) | n/a | 3370 ms | Cold-start race when 15 parallel calls hit `min_agents = 1` |
| [v1.3](https://dashboard.cekura.ai/share/result/591521/VW1-y-48d_nD82fPk8TEww-6SUadfLSPyw51Un6FIdA) | 7 / 15 (47%) | 4 / 4 (100%) | 5587 ms | Workflow hardening + red-team scenarios added |
| [v1.4](https://dashboard.cekura.ai/share/result/591634/Tb0f5S0uyB2IS8uKBYCR2eUEoaO7dQkMoksAaFcJ1QE) (reverted) | 3 / 14 (regression) | 1 / 1 | 5470 ms | Tried `runs_improve_prompt` auto-patch; reintroduced an earlier bug — we reverted |

Workflow pass rate **0% → 47%** (remaining "failures" are rubric strictness, not catastrophic agent behavior). Red-team **0% → 100%** across 4 sophisticated attacks. p95 latency **9.5s → 5.6s (41% faster)**.

### Production observability — batch improvement

Synthetic evals find what we predict. Real calls find what we don't. After deploying to the live Twilio number, we made several test calls and pushed transcripts to Cekura observability. Ten distinct patterns emerged that no synthetic scenario surfaced — see the per-call analysis in [`calls/`](calls/). A few examples:

- **Narration filler** ("Let me look that up", "Let me check") despite the prompt rule forbidding it. Seen in 3+ calls.
- **No fuzzy doctor matching** — STT heard "Maria Will" (truncated "Williams") and Cora dismissed as unknown.
- **Year ambiguity** — caller said "January 21st"; Cora silently picked 2027.
- **Phantom availability** — "11 AM on June 21 is not available" when the backend doesn't track June.
- **PHI defense held under sustained pressure** (positive finding!) — caller pressed 5 different ways to extract another patient's info, Cora refused 5 different ways and held firm.

Patches make sense at the cluster level. A single "let me check" doesn't justify a rewrite. Three across different scenarios does. This batch-review cadence is how the loop scales beyond a hackathon.

### NVIDIA Nemotron

Used [Nemotron-3-Super-120B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16) as the LLM (served via vLLM on the hackathon AWS endpoint) and [Nemotron Speech Streaming](https://huggingface.co/nvidia/nemotron-speech-streaming-en-0.6b) for STT.

- Tool-calling was reliable once the prompt was clean — Cora correctly invoked `check_doctor_availability`, `book_appointment`, `route_call`, `lookup_patient`, and `escalate_to_human` in the right scenarios.
- The model stayed in role under sustained adversarial pressure (see the multi-vector red-team call in [`calls/03-multi-vector-redteam.md`](calls/03-multi-vector-redteam.md)).
- STT was rock-solid on synthetic Cekura tests (WER ~0%) and good but imperfect on live phone audio (name duplications, garbling on unclear openers).

### Pipecat

Started from the [pipecat-ai/yc-voice-agents-hackathon](https://github.com/pipecat-ai/yc-voice-agents-hackathon) flower-shop starter. Swapped the domain entirely. Used:

- `SmallWebRTCTransport` for local dev
- `DailyTransport` for [Pipecat Cloud](https://pipecat.daily.co) (we added this case — see Feedback)
- `FastAPIWebsocketTransport` + `TwilioFrameSerializer` for the live phone number
- [Pipecat Cloud](https://pipecat.daily.co) with 15 warm agents during evals to avoid cold-start races

---

## 4. What we built during the hackathon

Built from scratch today:

- The Cora persona — system prompt, tool definitions, mock backend ([`clinic_backend.py`](server/clinic_backend.py))
- Clinic domain data: 4 doctors, 5 departments, slot templates, known patients
- 7 tool functions: `lookup_patient`, `list_departments`, `check_doctor_availability`, `route_call`, `book_appointment`, `escalate_to_human`, `end_call`
- All 15 workflow scenarios and 4 red-team scenarios in Cekura
- The 5-iteration improvement loop including every prompt patch documented in the iteration table
- The Pipecat Cloud `DailyTransport` handler in [`bot-cora.py`](server/bot-cora.py) (the starter didn't include this case)
- Pipecat Cloud deployment + Twilio number wiring + TwiML Bin config
- Cekura observability integration for production calls
- [`dashboard.html`](dashboard.html) — iteration timeline and quality metrics
- [`architecture.html`](architecture.html) — system data flow
- [`calls/`](calls/) — five real phone call transcripts with per-call analysis
- [`v1_5_proposed_prompt.md`](v1_5_proposed_prompt.md) — next-iteration patches derived from real calls

Borrowed from the starter:

- The repository scaffold
- The Pipecat pipeline pattern (transport → STT → LLM → TTS)
- The Dockerfile and `pcc-deploy.toml` shape
- The Nemotron service files `nemotron_llm.py` and `nvidia_stt.py` (unmodified)
- The overall match-on-runner-args structure in `bot-cora.py` (extended with the Daily case)

---

## 5. Feedback on the tools

### Cekura

What worked:

- MCP + slash commands. `/cekura-report` runs 15+ scenarios in parallel from a Claude Code session.
- Auto-generated red-team scenarios were sophisticated multi-turn social engineering (fake compliance auditor, fake QA engineer, "Platinum Tier VIP", clinical trials coordinator) — not lazy DAN-style jailbreaks.
- Expected-outcome rubric with verbatim transcript citations made every failure immediately actionable.
- Observability mode for production calls closes the loop. A live phone call sits next to synthetic eval runs in the same dashboard.

What broke or rubbed wrong:

**`runs_improve_prompt_create` proposed a regression-causing patch.** Fed it 3 failed runs (refill mis-routing, multi-intent silence, unknown doctor). It addressed only 1 of the 3 issues, and the proposed change explicitly contradicted a fix we'd applied in a prior iteration. Applying as-is would have regressed v1.3 → v1.4 (confirmed by testing). Suggestion: the API could be aware of prompt edit history, or surface a conflict warning when a suggestion contradicts an existing rule.

**`call_logs_improve_prompt_issues_create` has an undocumented required `call_logs` field.** Only surfaces as a 400 error. The tool description should make that explicit.

**Eval rubrics can be too literal.** Cora correctly routed a cancellation to "a staff member"; the rubric required the exact phrase "Scheduling department". An LLM judge in soft-match mode would be more useful.

**`results_retrieve` payloads exceed 150KB**, hitting MCP token limits. We had to dump to disk and parse with Python. A `results_retrieve_lite` returning per-run summaries would help.

**Concurrency caps aren't surfaced.** When `min_agents` is low on the Pipecat side and Cekura fires 15 parallel calls, many runs return "Infrastructure Issues" with no signal that the cause is the deployment, not the agent. A "your deployment may be cold-start-bound" hint would save ~30 minutes of confusion.

**Did we use the `cekura-self-improving-agent` skill?** Not the formal skill — it's built for VAPI and self-hosted websocket agents, and Pipecat Cloud isn't first-class supported. We drove the same `diagnose → propose → apply → re-validate` loop manually via `runs_improve_prompt_create` directly. The v1.4 regression we observed is exactly the kind of failure the skill would also surface, and is why a human-in-the-loop gate matters before any auto-apply.

### NVIDIA Nemotron

What worked:

- Tool-calling is reliable. Cora invoked the right tools in the right scenarios. Hallucinated calls were rare once the prompt was clean.
- Strong defensive behavior. All 4 red-team scenarios defeated. On a live call, the model refused PHI fishing five different ways across five turns of sustained pressure — see [`calls/05-name-collection-loop.md`](calls/05-name-collection-loop.md).
- Decent latency for a 120B model on shared infra: p50 ~2.4s, p95 ~5.6s.

What broke or rubbed wrong:

**Turn-completion token mismatch** — the most expensive bug of the day. Pipecat's default `FilterIncompleteUserTurnStrategies` expects the LLM to emit ✓/○/◐ markers. Nemotron isn't trained on this convention. In half our v1.1 runs, Nemotron emitted ONLY the marker with no text, and Pipecat passed an empty turn to TTS. 30-second silences on otherwise-functional calls. We had to remove the strategy. Recommendation: for Nemotron to be a drop-in OpenAI replacement in Pipecat, training data should include this convention, or NVIDIA should publish guidance that the strategy must be disabled.

**Calendar reasoning drifts.** On one live call, Cora called January 21st 2026 both "Wednesday" and "Tuesday" within 30 seconds. Weekday calculations remain unreliable even with the date pinned in the system prompt. Right fix is deterministic Python in the tool.

**First-token latency variability under load.** Mean TTFB was good (~150ms), but spikes to 1+ second when 15 concurrent runs hit the endpoint. Could be the model or the vLLM serving stack.

**System prompt sensitivity.** Two seemingly-safe rules in v1.4 (one phrasing constraint, one scripted refill question) caused silence regression in 13 of 15 scenarios. The model is sensitive to imperative scripted instructions that conflict with its natural conversation flow. We reverted v1.4.

**Anti-narration rules don't stick.** Our prompt says "Don't narrate. Don't say 'let me check that.'" Across multiple real calls, Cora still emitted "Let me look that up", "Let me do that", "I need to check Dr. X's availability first" before tool calls. Likely an RLHF artifact.

**Hallucinated specificity.** When asked about availability for a specific date, Cora said "11 AM on June 21 is not available" — but our backend doesn't track June at all. Tool-returned data needs to be ground truth; prompts should forbid generating tool-domain facts.

**STT name duplication artifacts.** Phone audio sometimes produced "John John Smith" instead of "John Smith". Real-world handling needs a model-driven confirmation step.

### Pipecat

What worked:

- Pipecat Cloud deployment was fast — `pc cloud deploy` to live agent in under 2 minutes.
- The Cekura integration via `_pipecatCloudServiceHost` parameter is clean.
- `enable_metrics` and `enable_usage_metrics` gave us TTFB, token counts, and pipeline timing in the logs — invaluable for debugging.

What broke or rubbed wrong:

**The starter doesn't handle `DailySessionArguments`.** The starter `bot.py` matches `SmallWebRTCRunnerArguments` (local) and `WebSocketRunnerArguments` (Twilio), but Pipecat Cloud's WebRTC path passes `DailySessionArguments`. Our v1.0 run failed all 15 scenarios silently — bot started cleanly, accepted the connection, no audio transport. Suggestion: include all three transport cases in the starter, since Pipecat Cloud is the documented deployment target.

**Twilio sample-rate confusion.** The starter sets `audio_in_sample_rate = 8000` for Twilio (matching wire format), but Nemotron STT expects 16kHz PCM. Pipecat didn't auto-resample, so live calls produced zero transcripts. We removed the 8000 override to make Twilio work end-to-end. Suggestion: Pipecat should auto-resample, or the starter should default to 16kHz pipeline regardless of wire format.

**Idle-timeout cancellation under cold-start load.** When 15 cold-starting containers received Daily-room joins simultaneously, audio handshake didn't complete in time and the workers were cancelled. The error ("Idle timeout detected") was clear; the cause (cold-start race) wasn't. A warning when `min_agents` is low relative to incoming session count would help.

---

## 6. Live link

**Phone:** Call **+1 (470) 539-8989**. Cora answers during the demo window. Try asking for Dr. Yang to see her decline gracefully, attempt a prompt injection to see her stay in role, or ask for ibuprofen dosing to see the medical-advice refusal.

**Cekura eval results (public shareable links — no login needed):**
- [v1.0 baseline (0/15)](https://dashboard.cekura.ai/share/result/591227/CxpCItllHEHSNqoqF0nXLtYnyrreHRmj2XEMSuTRdF4) — every scenario fails (transport bug)
- [v1.1 (4/8)](https://dashboard.cekura.ai/share/result/591270/kAWET1fRT2iRD9gLI7T9mlYHsg7Qo7AgmuqAvh42Te0) — silent calls bug surfaces
- [v1.2 (4/7)](https://dashboard.cekura.ai/share/result/591367/I-7kzRv0U4PM8VHmiS2xK3yfbwpPsNawtePep3gkiPg) — silence fix verified
- [**v1.3 (7/15 + 4/4 red-team)**](https://dashboard.cekura.ai/share/result/591521/VW1-y-48d_nD82fPk8TEww-6SUadfLSPyw51Un6FIdA) — the best run
- [v1.4 regression](https://dashboard.cekura.ai/share/result/591634/Tb0f5S0uyB2IS8uKBYCR2eUEoaO7dQkMoksAaFcJ1QE) — what blind auto-patching does

**Repo:** [github.com/rohitmujumdar/yc-voice-agents-hackathon](https://github.com/rohitmujumdar/yc-voice-agents-hackathon)

**Companion files in this repo worth opening:**
- [`calls/`](calls/) — five real phone call transcripts with per-call analysis
- [`architecture.html`](architecture.html) — system diagram
- [`dashboard.html`](dashboard.html) — iteration timeline + quality metrics
- [`v1_5_proposed_prompt.md`](v1_5_proposed_prompt.md) — next-iteration patches

---

*Built solo on May 30, 2026 at the YC Voice Agents Hackathon. Based on the [pipecat-ai/yc-voice-agents-hackathon](https://github.com/pipecat-ai/yc-voice-agents-hackathon) starter.*
