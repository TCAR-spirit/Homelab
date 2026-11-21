# Bilbo — Voice Capture & Transcription: Decision Doc

**Status:** Architecture decided 2026-11-21. Implementation in progress.
**Owner:** Tristen. **Agent:** Bilbo Baggins (Session Scribe).
**Scope:** Give Bilbo his defining ability — attend an *Aethrys* D&D session in a
Discord **voice** channel, record it, transcribe it locally, and hand the
transcript to the (already-built) in-character Bilbo, who writes a faithful recap
draft into the vault.

This doc records the decisions and *why*, so the build has a rationale of record.

---

## The problem

Hermes/Discord bots cannot natively receive voice audio. The standard bot API is
text-oriented; receiving per-user audio from a voice channel requires a dedicated
voice-receive process. So Bilbo's voice ability is a **separate capture service**
that produces a transcript, which the existing text-path Bilbo then narrates. This
mirrors the fleet's house pattern: *deterministic capture feeds the reasoning agent.*

```
Discord voice channel
   -> [1] voice receiver (our discord.py service): per-speaker PCM capture
   -> [2] ffmpeg: per-speaker PCM -> 16kHz mono WAV
   -> [3] whisper.cpp (LOCAL, on debian VM): WAV -> text, per speaker
   -> [4] merge + timestamp -> one speaker-tagged transcript .txt
   -> [5] in-character Bilbo reads it -> draft recap in vault 41 - Session Notes
```

Steps 1–4 are mechanical and must be reliable (they are the "ground truth").
Step 5 is judgment — the chronicler's craft — and is already built & tested.

---

## Decisions

### D1 — Transcription runs LOCALLY (whisper.cpp on the debian VM)
**Chosen over** a hosted STT API.
- **Why:** Privacy — the players' table audio never leaves the box. Free (no
  per-minute API cost). Fits the homelab ethos and the "it's our infrastructure"
  portfolio story.
- **Cost:** CPU time + we manage the model. Acceptable (see benchmark).

### D2 — Self-hosted voice receiver (discord.py), NOT Craig
**Chosen over** the third-party Craig recorder bot.
- **Why:** Full control, per-speaker streams by construction (needed for speaker
  attribution), no third-party bot in the server, and it is **our code in the repo**
  — a genuine portfolio piece (a Discord voice-capture → local-STT pipeline).
- **Cost / risk:** Discord voice-*receive* in discord.py relies on a community
  voice-receive extension (the core lib is send-focused). This is the highest-risk
  part of the build and is called out honestly as such.

### D3 — Per-speaker capture for speaker attribution
Discord voice delivers a separate audio stream per user (SSRC -> user id). We keep
streams separate end to end, transcribe each independently, then merge by timestamp.
That yields "**[Harmony] we head for the gates**" rather than an anonymous wall of
text — which is what makes a recap actually useful.

### D4 — Model: small.en (base.en as fast fallback)
Benchmarked on the actual VM (i7-8700T, 4 cores, AVX2/F16C/FMA, 4 threads):

| Model     | Size | Realtime factor | 3-hr session transcribes in |
|-----------|------|-----------------|-----------------------------|
| base.en   | 142M | 0.12x           | ~22 min                     |
| small.en  | 466M | 0.45x           | ~80 min                     |

**Chosen: small.en.** D&D audio is hard (overlap, dice, accents, invented fantasy
names like *Aethrys, Sorien, Xaden*). small.en is materially more accurate and still
transcribes a 3-hour session in ~80 min — fine, because transcription runs **after**
the session, not live. Accuracy beats speed for a faithful chronicle. base.en stays
as the fast fallback for quick tests.

### D5 — Post-session, not live
Transcription is a batch job after the session ends. The receiver records live; the
whisper pass runs afterward. No need for real-time STT, which would be far harder and
less accurate.

### D6 — Consent: table is aware (confirmed 2026-11-21)
Players know and are fine with recording. As hygiene, the receiver still posts a
"📝 Bilbo is now recording this session" notice in #chronicle when it joins the voice
channel, and a "recording stopped" notice when it leaves. Audio stays on the VM.

---

## System dependencies (installed 2026-11-21 on debian VM)
`cmake`, `ffmpeg`, `libopus-dev`/`libopus0` (decode Discord Opus),
`libsodium-dev` (Discord voice encryption). gcc/g++/make/git already present.
whisper.cpp built with `-march=native` (uses AVX2). Build + models live under
`~/bilbo-voice/tools/whisper.cpp` (not committed — external; we commit our code only).

---

## Lane & safety (unchanged from Bilbo's charter)
- The capture service writes only audio + transcripts under its own working dir.
- Only the in-character Bilbo writes to the vault, and only **draft** recaps into
  `40 - Campaign/41 - Session Notes/`. Never canon, never Gandalf's `_Proposals/`.
- The Iron Law holds *because* of this pipeline: Bilbo can only narrate what the
  microphone actually captured. No transcript line = he says the record is silent.

---

## Build status
- [x] System deps installed; whisper.cpp built & benchmarked on the VM.
- [x] Model chosen (small.en) with real RTF data.
- [ ] Voice receiver service (discord.py per-speaker capture) — **next**.
- [ ] Glue: receiver output -> ffmpeg -> whisper.cpp -> merged speaker-tagged transcript.
- [ ] End-to-end test: live session -> transcript -> Bilbo draft recap in the vault.

## Open risks (honest)
- discord.py voice-receive is community-maintained; may need version pinning/fiddling.
- Overlapping speech still degrades any STT; per-speaker streams mitigate but don't
  eliminate it.
- Long sessions = large audio; plan retention/cleanup of raw audio after transcription.
