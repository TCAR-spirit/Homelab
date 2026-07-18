# Zordon v0.1 — Initial Build and Container Troubleshooting

**Date:** 2026-07-17

## Goal
Stand up the first version of Zordon, a Discord bot that acts as a D&D
world-building assistant. On a schedule it asks lore questions, logs my
answers, and references an LLM so each new question builds on the
accumulated lore.

## What I did
- Installed Docker Desktop
- Built a container to host the bot and connect it to an LLM backend
  (OpenRouter, running Hermes)
- Configured the bot's Discord application, token, and channel ID

## Issues encountered

**1. Commands run from the wrong directory**
`docker compose up` returned `no configuration file provided: not found`.
The terminal was sitting in the user home directory rather than the project
folder, so Docker couldn't find `docker-compose.yml`.
*Fix:* used `cd` to move into the project directory before running compose
commands.

**2. Missing prompt file inside the container**
The container built successfully but crash-looped on startup with
`FileNotFoundError: '/app/zordon/prompts/zordon_system.txt'`. The `prompts`
folder had not been extracted with the rest of the project files, so the
bot's system prompt was missing.
*Fix:* recreated the `prompts` directory and its `zordon_system.txt` file,
verified the contents with `type`, then rebuilt the container.

**3. Environment file saved with wrong extension**
Windows saved the config file as `.env.txt`, which the application could not
read.
*Fix:* renamed the file to `.env`.

## Outcome
Container is up and running, connected to Discord, and responding to the
`!ask` command with in-character world-building questions.

## Takeaways
- Docker Compose commands must be run from the directory containing
  `docker-compose.yml`
- Container crash loops are best diagnosed by reading the full traceback in
  `docker compose logs -f` — the final line names the actual failure
- Verify file paths and extensions on Windows before building; hidden
  extensions are an easy source of "file not found" errors
