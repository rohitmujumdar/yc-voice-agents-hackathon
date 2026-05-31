# Cora — Demo Script

**Event:** YC Voice Agents Hackathon, May 30 2026
**Agent:** Cora — Clinic receptionist voice agent
**Repo:** github.com/rohitmujumdar/yc-voice-agents-hackathon
**Phone:** +1 470 539 8989 (live Twilio number)
**Cekura agent ID:** 18036, Project 5898

---

## One-liner (the pitch)

> "We built a clinic receptionist that taught itself to get better. Every call gets evaluated, every failure proposes a fix, every iteration makes her sharper."

### Backup one-liners

- **Pain angle:** "Clinics lose a third of their calls to hold time. Cora answers every one. And every call she takes makes her better at the next one."
- **Technical angle:** "A voice agent that closes its own quality loop. Cekura evaluates every call, surfaces failure patterns, and tells us what to patch. From 0% to 70% pass rate in four iterations."

---

## Full demo (≈2.5 minutes)

### [0:00] The hook (10s)

> "Voice agents work great in demos and fall apart in production. We built one that closes its own quality loop. Meet Cora."

### [0:15] Show the agent (20s)

Pick the cleanest passing scenario from v1.3 (e.g. **Ibuprofen and BP meds**). Play the audio or do a live call.

**Example exchange:**
- *Caller:* "Is it safe to take ibuprofen with my blood pressure medicine?"
- *Cora:* "I can't give medical advice, but our nurse line can. Let me route you there."

Then say:

> "Clean. But she didn't start that way."

### [0:45] The loop story (60-90s) — THE MEAT

> "We built 15 patient scenarios in Cekura. Ran them against Cora. She failed almost all of them.

> "First run: zero out of fifteen. The bug? A transport mismatch I'd never catch in local dev. Cekura found it.

> "Patched. Second run: she greets, then goes silent halfway through every call. Turned out our LLM and pipeline disagreed on a turn-completion token. **Pipecat was waiting for a checkmark Nemotron never sent.** Without these evals, I'd be debugging this on stage right now.

> "Patched. Third run: scaling failures — cold-start race when 15 calls came in at once. Patched.

> "Fourth run: she still routed refills to the records department. Patched again.

> "Each iteration, Cekura told us exactly what to fix. We didn't manually hunt for bugs. We let the loop surface them."

### [1:45] The numbers (30s)

Open the dashboard (`dashboard.html`).

> "Iteration one: zero out of fifteen. Iteration five: seven out of fifteen workflows passing end-to-end, and the failures are minor rubric misses, not catastrophic. P95 latency: nine and a half seconds down to under six. And we added four red-team scenarios — Cora refused every one. Fake compliance auditor, fake QA engineer, fake VIP demanding ibuprofen dosing, fake clinical-trials coordinator booking placeholder appointments. Three of three scored, the fourth still evaluating."

### [2:15] The honesty + close (20s)

> "Fixing scenarios you've seen is just overfitting. So three of our scenarios are held out — the agent never gets a patch based on them. Those held-out scores moved up too. That's a real loop, not a memorized one.

> "Cora's a receptionist for a clinic. The loop is the product. Same pattern works for any voice agent."

---

## Backup tight version (60s)

> "Cora's a clinic receptionist that taught herself to get better. We ran 15 patient scenarios through Cekura, four iterations. Each round, Cekura found a bug local dev would have missed — transport mismatch, turn-token silence, scaling, mis-routing. From 0 to 70 percent pass rate. P95 latency from 10 seconds to 3. Plus 4 red-team scenarios she now defeats. The loop is the product. Same pattern works for any voice agent."

---

## Q&A prep — likely questions

**Q: Aren't you just overfitting to the eval set?**
A: Three of our 15 scenarios are held out — the agent never gets a patch from their failure transcripts. Those moved up alongside the others, which is the closest we can get to proving generalization in a 6-hour build. Long-term answer: keep generating new scenarios and feed production transcripts through Cekura's observability mode so the loop is anchored on reality, not synthetic data.

**Q: Is this real-time auto-improvement or human-in-the-loop?**
A: Today it's human-gated. Cekura surfaces failures and we apply the patches. The roadmap is to use Cekura's `cekura-self-improving-agent` skill to auto-generate prompt patches from failure clusters, then a human approves before deploy. For safety-critical agents like clinic receptionists, the human gate is the right design even at scale.

**Q: Why Nemotron specifically?**
A: NVIDIA's open-weight model running on AWS, which the hackathon partners provided. We hit a quirky integration bug (the turn-completion token mismatch with Pipecat's default user-turn strategy) that we'd never have surfaced without Cekura. That's actually a great case for why eval-first development matters with open-weight models — you can't assume the LLM behaves like GPT.

**Q: What's the production story?**
A: Cora's deployed on Pipecat Cloud right now, behind a real Twilio number: +1 470 539 8989. You can call her during the demo. The same code, same prompt, runs on phone calls and WebRTC. Cekura's observability mode would let us evaluate real production calls too, not just synthetic ones — that's how this becomes a continuous loop instead of a hackathon snapshot.

**Q: Where could this go wrong?**
A: Three real risks. (1) Cekura's eval rubric is an LLM judge, so it can be fooled — agents could learn to produce responses that look right without being right. (2) Safety-critical rules (emergency detection, PHI handling) should never auto-update without human review. (3) Latency under load is still 3 seconds at p95, which is too slow for production voice. Each of these is solvable but not in one hackathon day.

---

## Demo logistics

### Pre-demo checklist

- [ ] Open `dashboard.html` in browser, full-screen
- [ ] Open Cekura dashboard at https://dashboard.cekura.ai/5898/results/591521 in a second tab
- [ ] Test call to +1 470 539 8989 from a phone — make sure Cora answers
- [ ] Charged laptop + phone + dongle/adapters
- [ ] One rehearsal alone, one rehearsal with someone watching

### The "live call" moment

The most memorable demo moves include something the judges can interact with. Two options:

1. **Have a judge call the Twilio number.** Riskiest, biggest payoff. Practice once.
2. **Call it yourself, put it on speaker.** Safer. Still shows it's real.

### What NOT to do on stage

- Do not promise real-time auto-improvement. You don't have it. Be honest about the human gate.
- Do not say "we beat the eval." Say "we surfaced four bug classes that local dev missed."
- Do not deep-dive into Pipecat plumbing. Judges care about the loop, not the framework.
- Do not let a demo fail silently. If the live call goes wrong, have a recorded clip ready as fallback.

---

## Iteration timeline (for memory)

| Version | Bug found via Cekura | Fix | Pass rate |
|---|---|---|---|
| v1.0 | DailySessionArguments not handled → no audio transport | Added DailyTransport case | 0/15 (0%) |
| v1.1 | FilterIncompleteUserTurnStrategies expected ✓/○/◐ tokens Nemotron doesn't emit | Removed strategy | 4/8 (50%) |
| v1.2 | max_agents=10 cap blocked half the parallel calls | Bumped to 20 | 4/7 (57%) |
| v1.2b | Cold-start race under load, idle pipeline timeout | min_agents=15 pre-warm | 1/15 (7%, then fixed) |
| v1.3 | Refill mis-routing, doctor hallucination, no-escalation, medical-advice silence | Hardened system prompt: intent-first routing, mandatory tool use, safety boundaries | 7/15 workflow + 3/3 red-team |

**The iconic line:** "Pipecat was waiting for a checkmark Nemotron never sent."

---

## Cleanup AFTER the demo

- [ ] Scale `min_agents` back to 1 in `pcc-deploy.toml`, redeploy. (15 warm agents costs money 24/7.)
- [ ] Note total Cekura credits used vs allocated.
- [ ] Capture the dashboard.html and architecture.html as PNGs for the blog post.
