import json
from datetime import datetime, timezone

import anthropic
from bctone.prompts.system import SYSTEM_PROMPT, CLASSIFY_PROMPT, ESCALATION_PROMPT, TODO_PARSE_PROMPT

MODEL_SONNET = "claude-sonnet-4-20250514"
MODEL_OPUS = "claude-opus-4-20250514"

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def classify_message(message: str) -> str:
    """Classify a message as PROGRESS, DECISION, or NONE."""
    client = get_client()
    response = client.messages.create(
        model=MODEL_SONNET,
        max_tokens=10,
        messages=[{"role": "user", "content": CLASSIFY_PROMPT.format(message=message)}],
    )
    result = response.content[0].text.strip().upper()
    if result not in ("PROGRESS", "DECISION", "TODO", "NONE"):
        return "NONE"
    return result


def should_escalate(message: str) -> bool:
    """Determine if a message requires Opus (complex) or Sonnet (simple)."""
    client = get_client()
    response = client.messages.create(
        model=MODEL_SONNET,
        max_tokens=10,
        messages=[{"role": "user", "content": ESCALATION_PROMPT.format(message=message)}],
    )
    return response.content[0].text.strip().upper() == "COMPLEX"


def chat(user_message: str, conversation_history: list[dict]) -> str:
    """Send a message to Claude with conversation history. Auto-routes Sonnet/Opus."""
    client = get_client()
    escalate = should_escalate(user_message)
    model = MODEL_OPUS if escalate else MODEL_SONNET

    messages = []
    for entry in conversation_history:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


def parse_todo(message: str) -> dict:
    """Extract TODO info (content, assignee, due_date) from a message."""
    client = get_client()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    response = client.messages.create(
        model=MODEL_SONNET,
        max_tokens=256,
        messages=[{"role": "user", "content": TODO_PARSE_PROMPT.format(message=message, today=today)}],
    )
    try:
        return json.loads(response.content[0].text.strip())
    except json.JSONDecodeError:
        return {"content": message, "assignee": None, "due_date": None}


def summarize(text: str, instruction: str) -> str:
    """Summarize text with a specific instruction. Always uses Sonnet."""
    client = get_client()
    response = client.messages.create(
        model=MODEL_SONNET,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"{instruction}\n\n{text}"}],
    )
    return response.content[0].text
