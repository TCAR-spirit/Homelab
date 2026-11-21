# Bilbo — Voice Capture & Transcription

Self-hosted Discord voice-capture → local speech-to-text pipeline for **Bilbo
Baggins**, the Session Scribe of the Command Center home-lab agent fleet. Bilbo
joins an *Aethrys* D&D session's voice channel, records each speaker separately,
transcribes the session **locally** (no audio leaves the box), and hands a
speaker-tagged transcript to the in-character Bilbo agent, who writes a faithful
recap **draft** into the campaign vault.

> Design rationale and the decisions behind this build: [`DECISION-DOC.md`](DECISION-DOC.md)

## Pipeline

```
Discord voice channel
  → bilbo_voice_receiver.py   (Py-cord; per-speaker WAV capture; consent notice)
  → transcribe.sh             (ffmpeg → whisper.cpp, local, small.en)
  → transcript.txt            (speaker-tagged, time-ordered — the ground truth)
  → in-character Bilbo agent  (writes a DRAFT recap into the vault)
```

The split is deliberate: **capture is mechanical and must be reliable; the
chronicle is judgment.** Only the agent writes to the vault, and only draft
recaps into `40 - Campaign/41 - Session Notes/` — never canon.

## Components

| File | What it does |
|------|--------------|
| `bilbo_voice_receiver.py` | Py-cord bot (shares Bilbo's identity). `!bilbo join` / `stop` / `status`. Records one WAV per speaker, announces when recording. |
| `transcribe.sh` | Turns a session dir of per-speaker WAVs into one merged, timestamped, speaker-tagged `transcript.txt` via ffmpeg + whisper.cpp. |
| `DECISION-DOC.md` | Architecture of record: why local STT, why self-hosted capture, model choice with real benchmarks, consent. |

## Why these choices (short version)

- **Local whisper.cpp** (not a hosted API): players' audio never leaves the VM; free.
- **Self-hosted Py-cord receiver** (not Craig): per-speaker streams for speaker
  attribution, and it's our code. Py-cord's `WaveSink` gives per-user recording
  out of the box (more stable than discord.py's experimental voice-recv ext).
- **small.en model**: benchmarked on the VM (i7-8700T) at ~0.45× realtime — a
  3-hour session transcribes in ~80 min, run after play. Accuracy over speed,
  because a chronicle must be faithful. (`base.en` is the fast fallback at ~0.12×.)

## Setup (on the debian VM)

System deps (installed once): `cmake ffmpeg libopus-dev libopus0 libsodium-dev`.

```bash
# 1. whisper.cpp (built with -march=native; AVX2)
#    lives at ~/bilbo-voice/tools/whisper.cpp with models/ggml-small.en.bin
# 2. receiver venv (isolated — Py-cord can't share Hermes' discord.py)
python3 -m venv ~/bilbo-voice/venv
~/bilbo-voice/venv/bin/pip install -r requirements.txt
```

The receiver reads Bilbo's bot token from his Hermes profile
`~/.hermes/profiles/bilbo/.env` (`DISCORD_BOT_TOKEN`).

## Usage

**The receiver runs as an always-on systemd user service** (`bilbo-voice.service`),
so it survives reboots and auto-restarts on failure. It's already enabled on the VM.

```bash
# service management (on the VM)
systemctl --user status  bilbo-voice      # is it running?
systemctl --user restart bilbo-voice      # restart after a code change
journalctl --user -u bilbo-voice -f       # live logs
```

Recording a session — type ONE word in Bilbo's **#chronicler text channel** while
you are sitting in the **voice channel** you want recorded:

| You type (in #chronicler) | What happens |
|---|---|
| **`!record`** | Bilbo joins your current voice channel, announces recording, captures per-speaker audio |
| **`!stop`** | Stops; saves per-speaker WAVs to `~/bilbo-voice/sessions/session_<ts>/` |
| **`!status`** | Reports whether he's recording and for how long |

Commands are forgiving: `!record` / `record` / `!rec` / `start` all begin;
`!stop` / `stop` / `done` all end. Normal chatter in the channel is ignored.

After the session, transcribe and hand off to the agent:
```bash
./transcribe.sh ~/bilbo-voice/sessions/session_<timestamp>
bilbo -z "Write a session recap draft from this transcript: $(cat .../transcript.txt)"
```

## Status

Pipeline proven end-to-end on 2026-11-21 (capture code + ffmpeg + whisper +
agent hand-off all tested). The one unproven link is the **live Discord voice
join**, which needs Bilbo's bot token in his profile `.env` and a real voice
session. See the profile's `GO-LIVE-RUNBOOK.md`.

## Privacy & consent

Table audio is transcribed locally and never sent off-box. The receiver
announces when it starts/stops recording. Raw audio should be cleaned up after
transcription (retention policy TBD).

---

*Part of the Command Center home-lab agent fleet. Built with Hermes as orchestrator.*
