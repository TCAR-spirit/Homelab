"""The lore store: an append-only markdown file of every question and answer.

Markdown (instead of a database) is deliberate for v0.1 -- you can read it,
edit it, and commit it to a private repo. If it ever outgrows this, the
functions below are the only thing that needs to change.
"""
from datetime import datetime

from . import config


def _ensure() -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not config.LORE_FILE.exists():
        config.LORE_FILE.write_text("# Campaign Lore Log\n", encoding="utf-8")


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def log_question(text: str) -> None:
    _ensure()
    with config.LORE_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n**Zordon ({_stamp()}):** {text}\n")


def log_answer(text: str) -> None:
    _ensure()
    with config.LORE_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n**World Smith ({_stamp()}):** {text}\n")


def recent(max_chars: int = 6000) -> str:
    """Return the tail of the lore log to use as LLM context."""
    _ensure()
    text = config.LORE_FILE.read_text(encoding="utf-8")
    return text[-max_chars:]
