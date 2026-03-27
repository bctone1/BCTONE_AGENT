from bctone.services.llm import classify_message, summarize as llm_summarize
from bctone.services.memory import save_memory


def handle_message(event: dict):
    """Silently collect messages and save progress/decisions to memory."""
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

    # Classify the message
    category = classify_message(text)

    if category == "NONE":
        return

    # Generate a summary
    summary = llm_summarize(text, "다음 메시지를 한 줄로 요약해주세요.")

    # Save to memory
    if category == "PROGRESS":
        save_memory(
            category="progress",
            source_user=user,
            source_channel=channel,
            content=text,
            summary=summary,
            expiry_days=14,
        )
    elif category == "DECISION":
        save_memory(
            category="decision",
            source_user=user,
            source_channel=channel,
            content=text,
            summary=summary,
        )
