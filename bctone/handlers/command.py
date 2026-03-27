from bctone.services.summarizer import summarize_team_progress, summarize_github

HELP_TEXT = """사용 가능한 명령어:

• `/bctone 요약` — 최근 팀 진행상황 요약
• `/bctone github backend` — 백엔드 레포 최근 변경 요약
• `/bctone github frontend` — 프론트엔드 레포 최근 변경 요약
• `/bctone github` — 양쪽 레포 요약
"""


def handle_command(ack, respond, command: dict):
    """Handle /bctone slash commands."""
    ack()

    text = command.get("text", "").strip()

    if not text:
        respond(text=HELP_TEXT)
        return

    if text == "요약":
        result = summarize_team_progress()
        respond(text=result)
        return

    if text.startswith("github"):
        parts = text.split()
        if len(parts) >= 2 and parts[1] in ("backend", "frontend"):
            result = summarize_github(parts[1])
            respond(text=result)
        else:
            backend = summarize_github("backend")
            frontend = summarize_github("frontend")
            respond(text=f"■ 백엔드\n{backend}\n\n■ 프론트엔드\n{frontend}")
        return

    respond(text=f"알 수 없는 명령입니다.\n\n{HELP_TEXT}")
