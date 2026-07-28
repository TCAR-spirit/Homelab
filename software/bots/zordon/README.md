# Zordon — D&D World-Building Assistant (bot repo)

This directory holds the code and deployment for **Zordon**, the Discord bot that
helps build my D&D campaign world. Design notes, architecture, and the original
build log live in the repo root at [`../software/Zordon.md`](../software/Zordon.md)
and the troubleshooting notes at [`../troubleshooting/zordon-v0.1.md`](../troubleshooting/zordon-v0.1.md).
This folder is the *runnable code*; that doc is the *design*.

## What's here

| File | Purpose |
|------|---------|
| `main.py` | Discord bot entrypoint, message routing (`!ask`, `!recap`) |
| `llm.py` | Backend-agnostic OpenAI-compatible LLM client |
| `scheduler.py` | APScheduler cron that posts one world-building question on a schedule |
| `data/lore.md` | Append-only lore log (gitignored locally, see note) |
| `docker-compose.yml` | Container deployment with auto-restart |
| `.env.example` | Template for required secrets |

## Run it

```bash
cp .env.example .env        # fill in DISCORD_TOKEN, ZORDON_CHANNEL_ID, LLM_API_KEY
sudo docker compose up -d --build
sudo docker compose logs -f # watch for "Zordon online as ..."
```

Without Docker: `pip install -r requirements.txt && python -m zordon.main`

## Roadmap (tracked in software/Zordon.md)
- [x] v0.1 — scheduled questions, lore log, in-character replies
- [ ] Obsidian vault link (read world lore for context)
- [ ] Weekly lore digest
- [ ] Migrate LLM backend to self-hosted Hermes on Proxmox
- [ ] Session transcription + TTS

## Note on the lore log
`data/lore.md` is the bot's working memory and is gitignored by default so raw
session output doesn't get committed. To snapshot canon lore into the repo, copy
the curated version into `../software/` or the Obsidian vault instead.
