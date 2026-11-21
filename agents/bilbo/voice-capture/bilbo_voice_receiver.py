#!/usr/bin/env python3
"""
Bilbo voice receiver — self-hosted Discord voice-capture service.

Part of the Command Center home-lab fleet. Bilbo Baggins (Session Scribe) joins
an Aethrys D&D session's Discord VOICE channel, records each speaker to a
separate WAV file, and (on stop) hands the audio to the local transcription
pipeline (ffmpeg -> whisper.cpp) which produces a speaker-tagged transcript. The
in-character Bilbo agent then turns that transcript into a draft session recap.

Design notes (see ../DECISION-DOC.md for the full rationale):
  - Per-SPEAKER capture (Py-cord WaveSink writes one file per user) so the
    transcript can be attributed ("[Harmony] we head for the gates").
  - LOCAL transcription only — audio never leaves the VM.
  - Consent: the table is aware; the bot still ANNOUNCES when it starts/stops
    recording as hygiene.
  - This service only writes audio + transcript artifacts under OUTPUT_ROOT. It
    NEVER writes to the vault. Only the in-character Bilbo agent writes recap
    drafts, and only into "40 - Campaign/41 - Session Notes/".

Commands (typed by Tristen in Bilbo's text channel, default #chronicle):
  !bilbo join      -> join the voice channel the caller is in; start recording
  !bilbo stop      -> stop recording, save per-speaker WAVs, kick off transcription
  !bilbo status    -> report whether a recording is in progress

Token: read from the bilbo Hermes profile .env (DISCORD_BOT_TOKEN) so this
service shares Bilbo's bot identity. It does NOT hardcode a token.

Run:  ~/bilbo-voice/venv/bin/python bilbo_voice_receiver.py
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import os
import pathlib
import sys

import discord

# --- configuration -----------------------------------------------------------

PROFILE_ENV = pathlib.Path.home() / ".hermes" / "profiles" / "bilbo" / ".env"
OUTPUT_ROOT = pathlib.Path.home() / "bilbo-voice" / "sessions"
COMMAND_PREFIX = "!bilbo"
# Optional: restrict command-listening to one text channel id (string). Empty = any.
COMMAND_CHANNEL_ID = os.environ.get("BILBO_COMMAND_CHANNEL_ID", "").strip()


def _load_token() -> str:
    """Read DISCORD_BOT_TOKEN from the bilbo profile .env without echoing it."""
    tok = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if tok:
        return tok
    if PROFILE_ENV.exists():
        for line in PROFILE_ENV.read_text().splitlines():
            if line.startswith("DISCORD_BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    print(
        f"ERROR: no DISCORD_BOT_TOKEN in env or {PROFILE_ENV}.\n"
        "Add Bilbo's bot token to his profile .env first (see GO-LIVE-RUNBOOK.md).",
        file=sys.stderr,
    )
    sys.exit(1)


# --- bot ---------------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True  # needed to read the !bilbo commands
intents.voice_states = True

bot = discord.Bot(intents=intents)

# guild_id -> dict(vc, sink, started_at, session_dir)
_active: dict[int, dict] = {}


def _session_dir() -> pathlib.Path:
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    d = OUTPUT_ROOT / f"session_{stamp}"
    d.mkdir(parents=True, exist_ok=True)
    return d


async def _finished_callback(sink: discord.sinks.WaveSink, session_dir: pathlib.Path,
                             text_channel: discord.TextChannel):
    """Called by Py-cord when recording stops: write per-speaker WAVs to disk."""
    written = []
    for user_id, audio in sink.audio_data.items():
        # Map user id -> a readable name if we can resolve the member.
        member = text_channel.guild.get_member(user_id)
        name = (member.display_name if member else str(user_id)).replace(" ", "_")
        out = session_dir / f"{user_id}__{name}.wav"
        with open(out, "wb") as f:
            f.write(audio.file.getbuffer())
        written.append(out.name)

    # Write a manifest so the transcription step knows speakers + order.
    manifest = session_dir / "MANIFEST.txt"
    manifest.write_text(
        "Bilbo session recording\n"
        f"recorded_at: {_dt.datetime.now().isoformat(timespec='seconds')}\n"
        f"speakers ({len(written)}):\n" + "\n".join(f"  - {w}" for w in written) + "\n"
        "\nNext: run transcribe.sh on this directory to produce transcript.txt,\n"
        "then hand transcript.txt to the in-character Bilbo agent for the recap draft.\n"
    )
    await text_channel.send(
        f"📝 Recording stopped. Saved **{len(written)}** speaker track(s) to "
        f"`{session_dir}`. I'll transcribe and write up the recap, Tristen."
    )


def _is_command_channel(message) -> bool:
    if not COMMAND_CHANNEL_ID:
        return True
    return str(message.channel.id) == COMMAND_CHANNEL_ID


@bot.event
async def on_ready():
    print(f"Bilbo voice receiver online as {bot.user} (id {bot.user.id})")
    print(f"Output root: {OUTPUT_ROOT}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.strip()
    if not content.startswith(COMMAND_PREFIX):
        return
    if not _is_command_channel(message):
        return

    arg = content[len(COMMAND_PREFIX):].strip().lower()
    guild = message.guild

    # --- join + start recording ---
    if arg in ("join", "listen", "record"):
        if guild.id in _active:
            await message.channel.send("I am already recording this session, my friend.")
            return
        if not (message.author.voice and message.author.voice.channel):
            await message.channel.send(
                "You'll need to be in a voice channel for me to join, Tristen."
            )
            return
        voice_channel = message.author.voice.channel
        try:
            vc = await voice_channel.connect()
        except Exception as e:  # noqa: BLE001 - surface the real error honestly
            await message.channel.send(f"I couldn't join the voice channel: `{e}`")
            return
        session_dir = _session_dir()
        sink = discord.sinks.WaveSink()
        vc.start_recording(sink, _finished_callback, session_dir, message.channel)
        _active[guild.id] = {
            "vc": vc, "sink": sink,
            "started_at": _dt.datetime.now(), "session_dir": session_dir,
        }
        await message.channel.send(
            "📝 *Bilbo settles in by the fire, quill ready.* I am now recording this "
            f"session in **{voice_channel.name}**. (The table knows; I keep an honest "
            "record.) Say `!bilbo stop` when the night is done."
        )

    # --- stop recording ---
    elif arg in ("stop", "done", "end"):
        state = _active.pop(guild.id, None)
        if not state:
            await message.channel.send("I'm not recording anything just now.")
            return
        state["vc"].stop_recording()  # triggers _finished_callback
        await state["vc"].disconnect()
        dur = _dt.datetime.now() - state["started_at"]
        await message.channel.send(
            f"That's the night set down — about {dur.seconds // 60} minutes recorded."
        )

    # --- status ---
    elif arg in ("status", "?"):
        state = _active.get(guild.id)
        if state:
            dur = _dt.datetime.now() - state["started_at"]
            await message.channel.send(
                f"Recording in progress — {dur.seconds // 60} min so far, "
                f"saving to `{state['session_dir'].name}`."
            )
        else:
            await message.channel.send("Not recording. Say `!bilbo join` to begin.")

    else:
        await message.channel.send(
            "I know `!bilbo join`, `!bilbo stop`, and `!bilbo status`, Tristen."
        )


if __name__ == "__main__":
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    bot.run(_load_token())
