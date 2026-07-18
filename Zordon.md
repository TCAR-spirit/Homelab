# Zordon — D&D World-Building Assistant
 
A Discord bot that helps me build my campaign world. On a schedule, Zordon
asks one world-building question. My answers accumulate in a lore log, and
every future question builds on that log — so over time he digs deeper into
the world instead of asking random questions.
this will also link to my already made Obsdian vault which houses all of my
already made lore and world building.
 
This is v0.1 (text only) of a larger project: the long-term goal is a
voice-capable assistant, self-hosted on my homelab, that also transcribes
and summarizes game sessions. See my [homelab repo](https://github.com/TCAR-spirit/Homelab)
for the infrastructure side.
 
## Architecture
 
```
APScheduler (cron) ──> llm.py ──> OpenAI-compatible endpoint
        │                              (OpenRouter + Hermes 4 today,
        v                               self-hosted Ollama later)
  Discord channel <──> main.py
        │
        v
  data/lore.md  (append-only lore log)
```
 
The LLM layer is deliberately backend-agnostic: `llm.py` speaks the
OpenAI-compatible API, so migrating from OpenRouter to a self-hosted
Hermes instance is a one-line `.env` change.
 
## Setup
 
### 1. Discord bot
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) → New Application → name it Zordon
2. **Bot** tab → Reset Token → copy it (this is `DISCORD_TOKEN`)(keep it handy)
3. Still on the Bot tab, enable **Message Content Intent** (required) it is directly above **Bot Permissions**
4. Then go to **OAuth2 → URL Generator**: check `bot` scope, then `Send Messages`,
   `Read Message History` permissions → open the generated URL and invite
   the bot to your server
5. Make a private channel (e.g. `#zordon`), then right-click it → Copy
   Channel ID (turn on Developer Mode in Discord settings if you don't see
   this)(keep channel ID handy). This is `ZORDON_CHANNEL_ID`.
### 2. LLM key
Create an account at [OpenRouter](https://openrouter.ai), add a few dollars
of credit, and make an API key (keep it handy). Hermes 4 70B costs ~$0.13/M input tokens —
this bot's usage rounds to pennies per month.
 
### 3. Run it
Now just fill in the .env file with all the corresponding ID number, api key, and bot token
once that is done make sure yopu have docker installed and up to date
finally in the docker CLI you can run these commands (make sure you are in the right directory when you run it)
```bash
docker compose up -d --build
docker compose logs -f  # watch for "Zordon online as ..."
```
 
Or without Docker: `pip install -r requirements.txt && python -m zordon.main`
 
### 4. Test
In the Zordon channel type `!ask` — he should respond with a question.
Answer it as a normal message; he'll acknowledge and log it. `!recap`
shows the recent lore log.
 
## Roadmap
- [x] v0.1 — scheduled questions, lore log, in-character replies
- [ ] Weekly lore digest (summarize the week's answers)
- [ ] Migrate LLM backend to self-hosted Hermes on Proxmox
- [ ] Session transcription (speech-to-text on recorded sessions)
- [ ] Zordon voice replies (TTS)
 
