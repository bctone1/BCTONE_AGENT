from bctone.services.summarizer import summarize_team_progress, summarize_github
from bctone.services.memory import get_todos, complete_todo

HELP_TEXT = """사용 가능한 명령어:

• `/bctone 요약` — 최근 팀 진행상황 요약
• `/bctone todo` — 미완료 할일 목록
• `/bctone todo done` — 완료된 할일 목록
• `/bctone todo 완료 #ID` — 할일 완료 처리
• `/bctone github backend` — 백엔드 레포 최근 변경 요약
• `/bctone github frontend` — 프론트엔드 레포 최근 변경 요약
• `/bctone github planning` — 기획 레포 최근 변경 요약
• `/bctone github` — 전체 레포 요약
"""


def _format_todos(todos: list[dict], title: str) -> str:
    if not todos:
        return f"{title}\n등록된 항목이 없습니다."

    lines = [title, ""]
    for t in todos:
        assignee = f"<@{t['assignee']}>" if t.get("assignee") else "미지정"
        due = t["due_date"].strftime("%m/%d") if t.get("due_date") else "기한 없음"
        status_icon = "done" if t["status"] == "done" else "open"
        summary = t.get("summary") or t["content"]
        lines.append(f"#{t['id']}  [{status_icon}]  {assignee} — {summary}  ({due})")

    return "\n".join(lines)


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

    if text.startswith("todo"):
        parts = text.split()

        # /bctone todo 완료 #3
        if len(parts) >= 3 and parts[1] == "완료":
            todo_id_str = parts[2].lstrip("#")
            try:
                todo_id = int(todo_id_str)
            except ValueError:
                respond(text="ID를 인식할 수 없습니다. 예: `/bctone todo 완료 #3`")
                return
            if complete_todo(todo_id):
                respond(text=f"#{todo_id} 할일을 완료 처리했습니다.")
            else:
                respond(text=f"#{todo_id}에 해당하는 할일을 찾지 못했습니다.")
            return

        # /bctone todo done
        if len(parts) >= 2 and parts[1] in ("done", "완료됨"):
            todos = get_todos(status="done")
            respond(text=_format_todos(todos, "■ 완료된 할일"))
            return

        # /bctone todo (default: open)
        todos = get_todos(status="open")
        respond(text=_format_todos(todos, "■ 미완료 할일"))
        return

    if text.startswith("github"):
        parts = text.split()
        if len(parts) >= 2 and parts[1] in ("backend", "frontend", "planning"):
            result = summarize_github(parts[1])
            respond(text=result)
        else:
            backend = summarize_github("backend")
            frontend = summarize_github("frontend")
            planning = summarize_github("planning")
            respond(text=f"■ 백엔드\n{backend}\n\n■ 프론트엔드\n{frontend}\n\n■ 기획\n{planning}")
        return

    respond(text=f"알 수 없는 명령입니다.\n\n{HELP_TEXT}")
