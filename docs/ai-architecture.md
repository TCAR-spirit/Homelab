# AI Architecture — Design Decisions

**Last updated:** 2026-10-28
**Status:** design settled, not yet implemented

How AI workloads are meant to run on this lab, and why. Written down because
these are the decisions that are expensive to reverse once several agents
depend on them — particularly anything touching cost.

**Primary constraint: keep token spend low.** The lab is always on, so agents
can act whenever, and most of what they do is not intellectually demanding.
Paying frontier-model rates for "what's on my calendar" is the failure mode
this design exists to prevent.

---

## 1. Hosting — orchestration here, inference elsewhere

**Decision: no local LLM for now.** Hermes and the agent containers run on
the Proxmox host; model inference goes out to a hosted API.

**Why not local inference on the EliteDesk:** the i7-8700T is a 35W 6-core
with no discrete GPU. CPU inference on a quantized 7–8B model lands around
3–6 tokens/sec — acceptable for an overnight batch job, unusable for
anything a Discord bot is waiting on. A model resident in RAM would also
consume 16–20GB of the host's 32GB, leaving nothing for the Omada
controller, Pi-hole, the portfolio site, and the agent containers.

**Where local inference goes when it happens:** the GPU node planned for
Phase 3, built around the existing RTX 3060 12GB. 12GB of VRAM holds a 7–14B
model at 4-bit quantization with real throughput. The EliteDesk Mini cannot
accept the card, so this is a separate chassis.

**Proxmox guest types:** services run as **LXC containers**, not full VMs —
Pi-hole, Omada controller, reverse proxy, monitoring. On a 32GB host that
distinction is most of the memory budget. Full VMs are reserved for things
that need kernel isolation, which in practice means the Hermes host.

---

## 2. Model routing — tiered, not a single backbone

**Decision: route per request rather than picking one model.** Any single
model as the default backbone is how token costs get away from you.

| Tier | Model | Work |
|---|---|---|
| 0 | Local (Phase 3+) | Intent classification, escalation triage, note summarization, transcript cleanup |
| 1 | Haiku 5.5 | Structured extraction, tool selection, routine lookups, alert triage |
| 2 | Sonnet 5.5 | Worldbuilding and lore continuity, vault synthesis |
| 3 | Opus 5.5 | Explicit escalation only — hard planning, multi-step reasoning |

**Default tier is Haiku 5.5.** This supersedes an initial plan to use Haiku
4.5, on pricing alone:

| | Input | Output |
|---|---|---|
| Haiku 4.5 | $1.00 / MTok | $5.00 / MTok |
| Haiku 5.5 (prompts ≤100k) | $0.10 / MTok | $0.50 / MTok |

Ten times cheaper and a newer model. Two caveats that shape the design:

- The cheap rate is tied to a **100,000-token prompt threshold**. Over it,
  Haiku 5.5 jumps to $0.50 / $2.50 per MTok. This is a direct argument for
  retrieving relevant context rather than dumping a whole vault into the
  prompt.
- Newer models use a tokenizer producing roughly **30% more tokens** for the
  same text, so the real-world saving is nearer 7–8× than 10×.

**Tier 0 decides the tier.** Once local inference exists, it is cheap enough
to run on every request, so it does triage and escalates only what needs it.
In a homelab the majority of agent traffic is trivial, and that traffic
should never reach a paid API.

---

## 3. Cost controls

Ranked by impact for this architecture specifically.

**1. Prompt caching.** The largest lever here, because agent harnesses
re-send the same system prompt and lore context every turn. A cache read on
Sonnet 5.5 costs $0.10 / MTok against $2.00 base input — a 20× reduction. A
5-minute cache write costs 1.25× base, so it pays for itself after a single
read. For a bursty conversational bot this is close to free money.

**2. Tiered routing**, per above. The spread between Haiku 5.5 input
($0.10 / MTok) and Opus 5.5 input ($4.00 / MTok) is 40×.

**3. Batch API — 50% off input and output**, and it stacks with caching.
Anything with no human waiting on it belongs here: session transcript
processing, proactive worldbuilding prompts, daily vault digests.

**4. Context hygiene.** The quiet killer. Retrieve relevant notes; never
dump the vault. An agent stuffing 40k tokens of lore into every turn costs
roughly 10× one that retrieves the right 4k — and risks crossing the Haiku
100k threshold into the expensive tier.

**5. Hard caps on agent iterations.** A ceiling on tool-call loops per
request. Runaway loops are the classic source of surprise homelab bills.

**6. Event-driven, never polling.** An agent waking on a 5-minute cron
costs ~8,600 API calls per month doing nothing. The same agent firing on
actual events costs a handful.

### Illustrative cost shape

Zordon at ~30 messages/day, ~8k context, ~500-token replies:

| Setup | Monthly |
|---|---|
| Opus 5.5, no caching | ~$38 |
| Sonnet 5.5 + caching | ~$7 |
| Above + Tier 0 triage absorbing the trivial half | ~$4 |

Rough figures, but the shape holds: caching and routing together are worth
roughly an order of magnitude.

---

## 4. Network monitoring — tooling detects, the model explains

**Decision: network agents are not agents.** An LLM polling the network and
deciding whether something is wrong is expensive, slower, and worse at the
job than purpose-built tooling.

```
Uptime Kuma / Zabbix / Omada alerts  →  detect, threshold, fire
                                        (free, deterministic, always on)
                      ↓  only when something fires
                 Haiku 5.5            →  triage, correlate, explain,
                                        write a readable alert
```

Monitoring is a solved problem that needs reliability, not intelligence. The
model's job is turning `re1 down, 3 failed DNS lookups, CPU 94%` into "your
WAN link dropped and Pi-hole is thrashing as a result — check the modem."
That is one API call when something actually breaks.

---

## 5. Worldbuilding assistant — four components, one of them a model

The hardest piece in the lab, and the difficulty is integration rather than
AI.

| Component | Choice | Cost |
|---|---|---|
| Discord voice capture | py-cord sinks (library support for voice *receiving* is the main integration risk) | — |
| Speech-to-text | **whisper.cpp, local, CPU** on the Proxmox host | Free |
| Reasoning | **Sonnet 5.5**, via the Batch API where possible | Low volume |
| Text-to-speech | **Piper, local, CPU** | Free |

**Transcription needs no GPU.** Sessions are processed after the fact, not
in real time, so slow is fine. `base` or `small` models are sufficient for
D&D audio. This is work the EliteDesk is genuinely good at, unlike LLM
inference. Live in-session transcription would require a hosted STT API;
batch Whisper is the right answer for notes and recaps.

**Reasoning is the one place to pay for a higher tier.** Creative continuity
and lore consistency is exactly where the tier difference shows. Volume is
low — once per session plus occasional lore chats — and post-session
transcript processing has no human waiting on it, making it an ideal Batch
API candidate.

**Voice:** Piper over a hosted TTS service, because the bot talks a lot and
per-character billing compounds. The character of the voice comes more from
processing than from the base model anyway — pitch down, reverb, slight ring
modulation.

**Recording consent:** Florida is an all-party consent state. Explicit
agreement from every player before the bot captures audio.

---

## 6. Instrumentation

**Log token usage per call from day one** — model, input tokens, cached
tokens, output tokens, and which agent — to local SQLite or Postgres.

You cannot optimize spend you cannot see, and "which bot is eating the
budget" is a question that arrives in month two, not month one.

---

## Open questions

- **OpenRouter vs direct API.** Hermes currently routes through OpenRouter.
  Prompt caching and the Batch API are the two largest cost levers here; if
  the abstraction layer does not pass them through cleanly, the convenience
  is being paid for in tokens. Worth verifying before volume grows.
- **Least-privilege scoping** across agent containers on limited hardware —
  one agent scoped to the NAS and servers, another to the Obsidian vault.
  Still unresolved.
- **Build order.** The network alerting agent should come first: it is the
  simplest end-to-end slice of the architecture — event fires, agent wakes,
  calls API, notifies — and it proves out Hermes, container scoping, and
  cost metering on a workload where mistakes are cheap. Worldbuilding last,
  once the plumbing is boring.

---

*Pricing figures are from Anthropic's published rates as of 2026-10 and
should be re-checked before relying on them.*
