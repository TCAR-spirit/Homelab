"""The LLM layer. This is the ONLY file that talks to a model.

It speaks the OpenAI-compatible chat API, which means the backend is
swappable via .env alone:

    OpenRouter (today)      LLM_BASE_URL=https://openrouter.ai/api/v1
    Ollama on the homelab   LLM_BASE_URL=http://<vm-ip>:11434/v1
"""
import re

from openai import AsyncOpenAI

from . import config

_client = AsyncOpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)

# Hermes 4 is a hybrid reasoning model and may emit <think>...</think> traces.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _clean(text: str) -> str:
    return _THINK_RE.sub("", text).strip()


async def _chat(user_content: str, max_tokens: int = 400) -> str:
    response = await _client.chat.completions.create(
        model=config.LLM_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    return _clean(response.choices[0].message.content)


async def generate_question(lore_context: str) -> str:
    prompt = (
        "Here is the campaign lore log so far (most recent at the bottom):\n\n"
        f"{lore_context}\n\n"
        "Ask the World Smith your next single world-building question."
    )
    return await _chat(prompt)


async def acknowledge(lore_context: str, answer: str) -> str:
    prompt = (
        "Here is the campaign lore log so far:\n\n"
        f"{lore_context}\n\n"
        f"The World Smith just answered: \"{answer}\"\n\n"
        "Give your brief in-character acknowledgment."
    )
    return await _chat(prompt, max_tokens=150)
