import re
from bctone.services.llm import classify_message, summarize as llm_summarize, parse_todo
from bctone.services.memory import save_memory, get_todos, complete_todo


def _check_todo_completion(text: str) -> int | None:
    """Check if a message marks a TODO as done (e.g. '완료 #3' or 'done #3')."""
    match = re.search(r"(?:완료|done|끝)\s*#?(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def handle_message(event: dict):
    """Silently collect messages and save progress/decisions/todos to memory."""
    # Ignore bot messages
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return

    text = event.get("text", "")
    user = event.get("user", "")
    channel = event.get("channel", "")

    if not text.strip():
        return

    # Skip if this is a mention (handled by mention handler)
    if "<@" in text:
        return

    # Check for TODO completion keyword
    todo_id = _check_todo_completion(text)
    if todo_id is not None:
        complete_todo(todo_id)
        return

    # Classify the message
    category = classify_message(text)

    if category == "NONE":
        return

    if category == "TODO":
        parsed = parse_todo(text)
        save_memory(
            category="todo",
            source_user=user,
            source_channel=channel,
            content=text,
            summary=parsed.get("content", text),
            assignee=parsed.get("assignee") or user,
            due_date=parsed.get("due_date"),
        )
    elif category == "PROGRESS":
        summary = llm_summarize(text, "다음 메시지를 한 줄로 요약해주세요.")
        save_memory(
            category="progress",
            source_user=user,
            source_channel=channel,
            content=text,
            summary=summary,
            expiry_days=14,
        )
    elif category == "DECISION":
        summary = llm_summarize(text, "다음 메시지를 한 줄로 요약해주세요.")
        save_memory(
            category="decision",
            source_user=user,
            source_channel=channel,
            content=text,
            summary=summary,
        )
