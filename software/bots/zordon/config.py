"""Central configuration. Everything comes from environment variables (.env file).

The LLM settings are the important part: point LLM_BASE_URL at OpenRouter today,
and at your self-hosted Ollama/llama.cpp endpoint tomorrow. Nothing else changes.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Discord ---
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["ZORDON_CHANNEL_ID"])

# --- LLM (OpenAI-compatible endpoint) ---
# Today:    https://openrouter.ai/api/v1  +  nousresearch/hermes-4-70b
# Someday:  http://<proxmox-vm-ip>:11434/v1  +  hermes4  (Ollama on the homelab)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_MODEL = os.getenv("LLM_MODEL", "nousresearch/hermes-4-70b")

# --- Schedule ---
# Default: 7:00 PM every Tuesday and Thursday (cron format: min hour day month weekday)
QUESTION_CRON = os.getenv("QUESTION_CRON", "0 19 * * 2,4")
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

# --- Storage ---
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
LORE_FILE = DATA_DIR / "lore.md"

SYSTEM_PROMPT = (
    Path(__file__).parent / "prompts" / "zordon_system.txt"
).read_text(encoding="utf-8")
