import re
from bctone.services.llm import chat
from bctone.services.memory import save_conversation, get_conversation_history


def handle_mention(event: dict, say):
    """Handle @비씨톤 mention events."""
    text = event.get("text", "")
    user = event.get("user", "")
    channel = event.get("channel", "")
    thread_ts = event.get("thread_ts", event.get("ts", ""))

    # Strip the bot mention from the message
    clean_text = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()

    if not clean_text:
        say(text="말씀해주시면 도움을 드리겠습니다.", thread_ts=thread_ts)
        return

    # Get conversation history for context
    history = get_conversation_history(channel_id=channel, thread_ts=thread_ts, limit=20)
    history_messages = [{"role": h["role"], "content": h["content"]} for h in reversed(history)]

    # Save user message to conversation history
    save_conversation(channel_id=channel, thread_ts=thread_ts, role="user", content=clean_text)

    # Get LLM response
    response = chat(clean_text, history_messages)

    # Save assistant response to conversation history
    save_conversation(channel_id=channel, thread_ts=thread_ts, role="assistant", content=response)

    say(text=response, thread_ts=thread_ts)
