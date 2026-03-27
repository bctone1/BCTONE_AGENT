import re
from bctone.services.llm import chat
from bctone.services.memory import save_conversation, get_conversation_history
from bctone.services.summarizer import summarize_github, summarize_team_progress

_GITHUB_PATTERN = re.compile(
    r"(github|깃허브|깃헙|커밋|commit|PR|풀리퀘|변경사항|머지|merge)",
    re.IGNORECASE,
)
_REPO_KEYWORDS = {
    "backend": re.compile(r"(백엔드|backend|서버)", re.IGNORECASE),
    "frontend": re.compile(r"(프론트|frontend|프론트엔드|클라이언트)", re.IGNORECASE),
    "planning": re.compile(r"(기획|planning|문서|docs)", re.IGNORECASE),
}
_SUMMARY_PATTERN = re.compile(
    r"(요약|진행.?상황|팀.?현황|리포트|보고)",
    re.IGNORECASE,
)


def _detect_github_intent(text: str) -> str | None:
    """Detect GitHub-related intent. Returns repo key or 'all', or None."""
    if not _GITHUB_PATTERN.search(text):
        return None
    for key, pattern in _REPO_KEYWORDS.items():
        if pattern.search(text):
            return key
    return "all"


def _detect_summary_intent(text: str) -> bool:
    """Detect team progress summary intent."""
    return bool(_SUMMARY_PATTERN.search(text) and not _GITHUB_PATTERN.search(text))


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

    # Check for GitHub intent — call API directly instead of LLM chat
    github_target = _detect_github_intent(clean_text)
    if github_target:
        if github_target == "all":
            backend = summarize_github("backend")
            frontend = summarize_github("frontend")
            planning = summarize_github("planning")
            response = f"■ 백엔드\n{backend}\n\n■ 프론트엔드\n{frontend}\n\n■ 기획\n{planning}"
        else:
            response = summarize_github(github_target)
        save_conversation(channel_id=channel, thread_ts=thread_ts, role="user", content=clean_text)
        save_conversation(channel_id=channel, thread_ts=thread_ts, role="assistant", content=response)
        say(text=response, thread_ts=thread_ts)
        return

    # Check for team progress summary intent
    if _detect_summary_intent(clean_text):
        response = summarize_team_progress()
        save_conversation(channel_id=channel, thread_ts=thread_ts, role="user", content=clean_text)
        save_conversation(channel_id=channel, thread_ts=thread_ts, role="assistant", content=response)
        say(text=response, thread_ts=thread_ts)
        return

    # Default: LLM chat
    history = get_conversation_history(channel_id=channel, thread_ts=thread_ts, limit=20)
    history_messages = [{"role": h["role"], "content": h["content"]} for h in reversed(history)]

    save_conversation(channel_id=channel, thread_ts=thread_ts, role="user", content=clean_text)

    response = chat(clean_text, history_messages)

    save_conversation(channel_id=channel, thread_ts=thread_ts, role="assistant", content=response)

    say(text=response, thread_ts=thread_ts)
