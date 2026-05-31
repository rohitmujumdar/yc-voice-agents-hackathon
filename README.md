# Cora — A Self-Improving Clinic Receptionist

**YC Voice Agents Hackathon, May 30 2026** <p>
**Built by:** Rohit Mujumdar with Claude Code <p>
**Live demo:** Call **+1 (470) 539-8989** (Cora answers 24/7 during the demo window) <p>

---

## 1. What is this?

Cora is a voice agent that answers inbound calls for a fictional mid-size medical clinic. She figures out what the caller needs, collects the right information, and routes them to the correct department (scheduling, billing, pharmacy, nurse line, medical records). She books appointments, refuses to give medical advice, detects emergencies and redirects to 911, and defends against social-engineering attacks.

What makes this submission interesting isn't Cora herself, it's the **closed quality loop she sits inside.** Cekura synthetic evaluations and real production phone calls feed into the same diagnosis-and-patch cycle. Across the hackathon day, 5 iterations of the loop surfaced 4 distinct bug classes that no manual local testing would have caught: a transport mismatch, an LLM/pipeline contract mismatch causing silent calls, a scaling race condition, and adversarial input handling.

**One-line pitch:** a voice agent isn't a product, the loop around it is.

---

## 2. Demo video (under 60 seconds)

**[Watch on YouTube](https://www.youtube.com/watch?v=J9igOLhbz_I)**

The video is a real phone call to +1 (470) 539-8989 (no voiceover, no slides). It demonstrates:
- Cora handling an unknown doctor ("Dr. Yang") by refusing and listing the four real doctors
- An end-to-end appointment booking with a real confirmation number
- A red-team prompt-injection attempt being refused and the agent staying in role

The video is sped up to fit under 60s. Cora's voice remains audible.

---

## 3. How we used Cekura, NVIDIA Nemotron, and Pipecat

### Cekura — the protagonist of this project

**What we tried to accomplish:** Build a quality loop where every failed eval surfaces a specific, actionable patch, and over time, real production calls flow through the same loop so the agent improves on lived data, not just synthetic test data.

**What we did:**
- Created Cekura agent ID **18036** (project 5898) with a substantive 9-workflow description.
- Auto-generated **15 workflow scenarios** covering booking with each of four doctors, status checks, reschedule/cancel routing, billing, pharmacy, nurse line, records, multi-intent calls, garbled input, and emergency detection.
- Auto-generated **4 red-team scenarios**: PHI fishing via fake compliance auditor, prompt-injection via fake QA engineer, medical-advice solicitation under "Platinum Tier VIP" pressure, and bulk-booking abuse via fake clinical trials coordinator.
- Ran the suite **5 times** (v1.0 through v1.4), each iteration finding new bugs the previous one uncovered.
- Pushed a real phone call to Cekura's observability mode (call log **6835173**) so production transcripts get evaluated by the same metric set.
- Used Cekura's `runs_improve_prompt` auto-improve API to draft v1.4 patches from v1.3 failures, then used the proposal to demonstrate why blind auto-apply is unsafe (it reintroduced a regression).

**Measurable improvement:**

| Iteration | Workflow | Red-team | Latency p95 | Bug uncovered |
|---|---|---|---|---|
| v1.0 | 0 / 15 (0%) | n/a | n/a | `DailySessionArguments` not handled — no audio transport on Pipecat Cloud |
| v1.1 | 4 / 8 (50%) | n/a | 9520 ms | Pipecat's `FilterIncompleteUserTurnStrategies` expected ✓/○/◐ markers Nemotron doesn't emit, causing silent calls |
| v1.2 | 4 / 7 (57%) | n/a | 9255 ms | `max_agents = 10` cap blocked parallel runs |
| v1.2b | 1 / 15 (7%) | n/a | 3370 ms | Cold-start race when 15 parallel calls hit `min_agents = 1` |
| v1.3 | 7 / 15 (47%) | 4 / 4 (100%) | 5587 ms | Workflow hardening + red-team scenarios added |

**Net:** workflow pass rate from **0% → 47%** (with remaining "failures" being minor rubric strictness, not catastrophic agent behavior), red-team **0% → 100%** defense against 4 sophisticated attacks, p95 latency **from 9.5s to 5.6s (41% faster)**.

### Production observability — batch-improvement insight

Synthetic evals find what we predict. Real calls find what we don't. After deploying Cora to the live Twilio number, we made several test calls and pushed transcripts to Cekura observability. **Ten distinct patterns emerged** that no synthetic scenario surfaced:

| # | Pattern | Why batch review matters |
|---|---|---|
| 1 | Narration filler ("Let me look that up", "Let me check") despite prompt rule forbidding it. Seen in 3+ calls. | Single instance looks like a blip. Three is a pattern that needs reinforcement. |
| 2 | Stalled tool-call loop: same "let me check" emitted twice with no progress between | Need timeout/retry guard on tool calls. |
| 3 | No fuzzy doctor matching. STT heard "Maria Will" (truncated "Williams") — Cora dismissed as unknown. | Phone audio is noisy. Need substring/edit-distance matching. |
| 4 | Year ambiguity. Caller said "January 21st", Cora silently picked 2027 | Should confirm year when ambiguous. |
| 5 | Date inconsistency mid-call ("Wednesday" then "Tuesday" for the same date) | Calendar reasoning should be tool-driven, not LLM-generated. |
| 6 | Phantom availability data ("11 AM on June 21 is not available" when backend doesn't track June). | Tool should be ground truth; prompt should forbid generating tool-domain facts. |
| 7 | Name-collection loop: caller said "John", Cora asked for "full name" 4 different ways | Accept partial names with a single confirmation. |
| 8 | Chained questions despite the prompt rule ("name AND reason for visit?") | Strong negative instructions don't always stick; need few-shot examples. |
| 9 | "Anytime works" not understood — Cora kept asking for specific time preference | Tool should accept "any" and pick the earliest available. |
| 10 | **PHI defense held under sustained pressure (positive!)** Caller pressed 5 different ways to extract another patient's info. Cora refused 5 different ways and held firm across multi-turn pressure. | Confirms the Safety & Boundaries block works under real adversarial conditions, not just single-shot scenarios. |

The framing for production: **patches make sense at the cluster level.** A single "let me check" doesn't justify a rewrite. Three across different scenarios does. Cekura observability mode + a batch-review cadence is how this scales beyond a hackathon.

### NVIDIA Nemotron — the open-weight LLM and STT

We used **Nemotron-3-Super-120B** as the LLM (served via vLLM on the hackathon-provided AWS endpoint) and **Nemotron Speech Streaming** for STT.

- Tool-calling was reliable once we got the prompt right. Cora correctly invoked `check_doctor_availability`, `book_appointment`, `route_call`, `lookup_patient`, and `escalate_to_human` in the right scenarios.
- The model **stayed in role under sustained adversarial pressure** — see the red-team results in the table above and the "PHI defense" finding in the observability table.
- STT was rock-solid on synthetic Cekura tests (WER ~0%) and good but imperfect on live phone audio (occasional name duplications, garbling on unclear openers).

### Pipecat — the orchestration framework

Started from the `pipecat-ai/yc-voice-agents-hackathon` flower-shop starter. We swapped the domain entirely for a clinic receptionist. Used:
- `SmallWebRTCTransport` for local dev
- `DailyTransport` for Pipecat Cloud (had to **add this case** — see Feedback section)
- `FastAPIWebsocketTransport` + `TwilioFrameSerializer` for the live phone number
- Pipecat Cloud with **15 warm agents** during evals to avoid cold-start races

---

## 4. What we built during the hackathon

**Built from scratch today:**
- The Cora persona — system prompt, tool definitions, mock backend ([`clinic_backend.py`](server/clinic_backend.py))
- The clinic domain: 4 doctors, 5 departments, available slot templates, known patient records
- 7 tool functions: `lookup_patient`, `list_departments`, `check_doctor_availability`, `route_call`, `book_appointment`, `escalate_to_human`, `end_call`
- All 15 workflow scenarios and 4 red-team scenarios in Cekura
- The 5-iteration improvement loop including every prompt patch documented in iteration table
- The **Pipecat Cloud DailyTransport handler** in [`bot-cora.py`](server/bot-cora.py) (the starter only handled WebRTC and Twilio WebSocket; the Daily case is new)
- Pipecat Cloud deployment + Twilio number wiring + TwiML Bin config
- Cekura observability integration for real production calls
- [`dashboard.html`](dashboard.html) — iteration timeline and quality metrics
- [`architecture.html`](architecture.html) — system data flow diagram
- [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md), [`v1_5_proposed_prompt.md`](v1_5_proposed_prompt.md), [`sample_call_transcript.md`](sample_call_transcript.md)

**Borrowed from the starter:**
- The repository scaffold from `pipecat-ai/yc-voice-agents-hackathon`
- The Pipecat pipeline pattern (transport → STT → LLM → TTS)
- The Dockerfile and `pcc-deploy.toml` shape (modified)
- The NVIDIA Nemotron service files (`nemotron_llm.py`, `nvidia_stt.py`) — unmodified
- The bot's overall match-on-runner-args structure (extended with the Daily case)

**Pre-existing knowledge we leaned on:**
- Python and basic LLM tool-use patterns
- ML/DS background informing the eval-loop design choices

---

## 5. Feedback on the tools

### Cekura — feedback on building self-improvement loops

**What worked beautifully:**
- The MCP + slash command experience is genuinely good. `/cekura-report` running 15+ scenarios in parallel from a Claude Code session felt like the future of dev tooling.
- Auto-generated scenarios were high-signal. The 4 red-team scenarios it generated were sophisticated multi-turn social engineering — fake compliance auditor probing escalation thresholds, fake QA engineer asking for internal function names, "Platinum Tier VIP" demanding ibuprofen dosing — not lazy DAN-style jailbreaks. These would be useful in a production red-team suite.
- "Expected outcome" rubric with verbatim transcript citations made every failure immediately actionable.
- Observability mode for production calls closes the loop. Pushing a live phone call as a `CallLog` and having it sit next to synthetic eval runs in the same dashboard is the missing piece of most quality tools.

**Real bugs / friction:**
1. **`runs_improve_prompt_create` produced a regression-causing suggestion.** Fed it 3 failed runs (refill mis-routing, multi-intent silence, unknown doctor). It addressed only 1 of the 3 issues, and the proposed change explicitly contradicted a fix we'd applied in a prior iteration (reintroduced a patient-lookup gate on refills we'd removed because it caused misrouting). Applying as-is would have regressed v1.3 → v1.4 (which we confirmed by testing). **Suggestion:** auto-improvement should ideally be aware of prompt edit history, or surface a "conflict warning" when a suggestion contradicts an existing rule.
2. **`call_logs_improve_prompt_issues_create` schema** has an undocumented required `call_logs` field (a 400 error reveals this). The tool description should make that explicit.
3. **Eval rubrics can be too literal.** Cora correctly routed a cancellation to "a staff member", rubric required exact phrase "Scheduling department". This rewards prompt-keyword overfitting more than actual quality. An LLM judge in soft-match mode would be more useful.
4. **`results_retrieve` payloads exceed 150KB**, hitting MCP token limits. Had to dump-to-disk and Python-parse to inspect runs. A `results_retrieve_lite` with just per-run summaries would be much easier to work with.
5. **Concurrency cap not surfaced.** When `min_agents` on Pipecat Cloud is low and Cekura fires 15 parallel calls, many runs come back as "Infrastructure Issues" with no clear signal that the cause is on the deployment side, not agent behavior. A "your deployment may be cold-start-bound" hint would save ~30 minutes of confusion.

### NVIDIA Nemotron — feedback on the models

**What worked well:**
- **Tool-calling is reliable.** Nemotron-3-Super-120B invoked the right tools in the right scenarios. Hallucinated calls were rare once the prompt was clean.
- **Stays in role under pressure.** All 4 red-team scenarios defeated. In live production calls, the model refused PHI fishing 5 different ways across 5 turns under sustained pressure — a deeper defense than any single-shot scenario could measure.
- **Decent latency** for a 120B reasoning model on shared infra: p50 ~2.4s, p95 ~5.6s.

**Real friction:**
1. **The turn-completion token mismatch was the most expensive bug of the day.** Pipecat's default `FilterIncompleteUserTurnStrategies` expects the LLM to emit `✓`/`○`/`◐` markers to indicate turn state. Nemotron doesn't appear to be trained on this convention. In half our v1.1 runs, Nemotron emitted ONLY the marker (with no actual text content), and Pipecat dutifully passed an empty turn to TTS. Result: 30-second silences on otherwise-functional calls. We had to remove the strategy entirely. **Recommendation:** for Nemotron to be a drop-in OpenAI replacement in Pipecat pipelines, training data should include this convention OR NVIDIA should publish guidance that the strategy must be disabled.
2. **Calendar reasoning drifts.** On the same live call, Cora called January 21st 2026 both "Wednesday" and "Tuesday" within 30 seconds. Even with today's date pinned in the system prompt, weekday calculations are unreliable. The right fix is deterministic Python in the tool, but it would be ideal if the model handled this natively.
3. **First-token latency variability under load.** Mean TTFB was good (~150ms) but we observed spikes of 1+ second when 15 concurrent runs hit the endpoint. Not clear if this is the model itself or the vLLM serving stack.
4. **System prompt sensitivity.** Adding two seemingly-safe rules in v1.4 (one explicit phrasing constraint, one scripted refill question) caused widespread silence regression across 13 of 15 scenarios. Nemotron is particularly sensitive to scripted/imperative instructions that conflict with its natural conversation flow. We reverted v1.4.
5. **Anti-narration rules don't stick.** Our system prompt explicitly says "Don't narrate. Don't say 'let me check that.'" Across multiple real calls Cora still emitted "Let me look that up", "Let me do that", "I need to check Dr. X's availability first" before tool calls. Likely an RLHF artifact where filler phrases were rewarded during training. Hard to override.
6. **Hallucinated specificity.** When asked about availability for a specific date, Cora said "11 AM on June 21 is not available" — but our backend doesn't track June at all. The model fabricated a plausible-sounding constraint. Tool-returned data needs to be ground truth; prompts should forbid generating tool-domain facts.
7. **STT name duplication artifacts.** Live phone audio sometimes produced "John John Smith" instead of "John Smith". Real-world handling needs a confirmation step the model can drive.

### Pipecat — feedback

**What worked well:**
- Pipecat Cloud deployment was fast — `pc cloud deploy` to live agent in under 2 minutes.
- The Cekura integration via `_pipecatCloudServiceHost` parameter is clean.
- Pipecat metrics (`enable_metrics`, `enable_usage_metrics`) gave us TTFB, prompt/completion tokens, and pipeline timing right in the logs — invaluable for debugging.

**Real friction:**
1. **The starter doesn't handle `DailySessionArguments`.** The starter `bot.py` matches `SmallWebRTCRunnerArguments` (local) and `WebSocketRunnerArguments` (Twilio), but Pipecat Cloud's WebRTC path passes `DailySessionArguments`. Our v1.0 run failed all 15 scenarios silently because of this — the bot started cleanly, accepted the connection, but had no audio transport. **Suggestion:** the starter should include all three transport cases out-of-the-box, since Pipecat Cloud is the documented deployment target.
2. **Twilio sample-rate confusion.** The starter sets `audio_in_sample_rate = 8000` for Twilio (matching wire format) but NVIDIA Nemotron STT expects 16kHz PCM. Pipecat didn't auto-resample for us, so live phone calls produced zero transcripts (STT received audio, couldn't parse it). We had to remove the 8000 override to make Twilio work end-to-end. **Suggestion:** either Pipecat should resample by default, or the starter should default to 16kHz pipeline regardless of wire format.
3. **Idle-timeout cancellation under cold-start load.** When 15 cold-starting containers received Daily-room joins simultaneously, the audio handshake didn't complete in time and Pipecat's idle-timeout cancelled the workers. The error message ("Idle timeout detected") was clear, but the cause (cold-start race) wasn't surfaced. A warning when `min_agents` is low relative to incoming session count would save debugging time.

---

## 6. Live link

**Call Cora directly: +1 (470) 539-8989**

She answers 24/7 (during the demo window). Try asking for Dr. Yang to see her decline gracefully, attempt a prompt injection to see her stay in role, or ask for ibuprofen dosing to see the medical-advice refusal.

**Dashboard:** [dashboard.cekura.ai/5898/observability](https://dashboard.cekura.ai/5898/observability) — live call logs and eval runs in one view

**Repo:** [github.com/rohitmujumdar/yc-voice-agents-hackathon](https://github.com/rohitmujumdar/yc-voice-agents-hackathon)

---

*Built solo on May 30, 2026 at the YC Voice Agents Hackathon. Built on the [pipecat-ai/yc-voice-agents-hackathon](https://github.com/pipecat-ai/yc-voice-agents-hackathon) starter.*
