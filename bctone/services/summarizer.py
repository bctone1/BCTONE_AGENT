import json
from datetime import datetime, timezone
from bctone.services.github_service import get_recent_prs, get_recent_commits
from bctone.services.memory import get_recent_memories, get_todos
from bctone.services.llm import summarize as llm_summarize


def summarize_github(repo_key: str, days: int = 1) -> str:
    """Summarize recent GitHub activity for a repo."""
    prs = get_recent_prs(repo_key, limit=10)
    commits = get_recent_commits(repo_key, days=days)

    repo_labels = {
        "backend": "백엔드 (GF_Backend)",
        "frontend": "프론트엔드 (GF_Frontend)",
        "planning": "기획 (mintlify-docs)",
    }
    repo_label = repo_labels.get(repo_key, repo_key)

    data = json.dumps({"PRs": prs, "commits": commits}, ensure_ascii=False, indent=2)
    instruction = (
        f"다음은 {repo_label} 레포의 최근 {days}일 GitHub 활동입니다. "
        "한국어로 간결하게 요약해주세요. PR 번호와 제목, 머지 여부, 주요 커밋을 포함하세요."
    )
    return llm_summarize(data, instruction)


def summarize_team_progress() -> str:
    """Summarize recent team progress from memory."""
    memories = get_recent_memories(limit=30)

    if not memories:
        return "최근 수집된 팀 진행상황이 없습니다."

    data = json.dumps(
        [{"category": m["category"], "content": m["content"], "summary": m.get("summary", "")} for m in memories],
        ensure_ascii=False,
        indent=2,
    )
    instruction = (
        "다음은 최근 팀에서 수집된 진행상황과 결정사항입니다. "
        "역할별(팀장/기획/프론트/백엔드)로 정리하고, 결정사항은 별도로 분류해주세요."
    )
    return llm_summarize(data, instruction)


def _format_todo_section() -> str:
    """Format open TODOs for reports."""
    todos = get_todos(status="open")
    if not todos:
        return "미완료 할일이 없습니다."

    lines = []
    for t in todos:
        assignee = t.get("assignee", "미지정")
        due = t["due_date"].strftime("%m/%d") if t.get("due_date") else "기한 없음"
        summary = t.get("summary") or t["content"]
        lines.append(f"• #{t['id']} {assignee} — {summary} ({due})")
    return "\n".join(lines)


def generate_daily_report() -> str:
    """Generate a daily report combining GitHub + team progress + TODOs."""
    backend_summary = summarize_github("backend", days=1)
    frontend_summary = summarize_github("frontend", days=1)
    planning_summary = summarize_github("planning", days=1)
    team_summary = summarize_team_progress()
    todo_section = _format_todo_section()

    today = datetime.now(timezone.utc).strftime("%Y년 %m월 %d일")

    combined = f"""일일 리포트 — {today}

■ 백엔드 (GF_Backend)
{backend_summary}

■ 프론트엔드 (GF_Frontend)
{frontend_summary}

■ 기획 (mintlify-docs)
{planning_summary}

■ 팀 진행상황
{team_summary}

■ 미완료 TODO
{todo_section}
"""

    instruction = "다음 일일 리포트를 깔끔하게 정리해주세요. 형식을 유지하되, 중복을 제거하고 핵심만 남겨주세요."
    return llm_summarize(combined, instruction)


def generate_weekly_report() -> str:
    """Generate a weekly report."""
    backend_summary = summarize_github("backend", days=7)
    frontend_summary = summarize_github("frontend", days=7)
    planning_summary = summarize_github("planning", days=7)
    team_summary = summarize_team_progress()
    todo_section = _format_todo_section()

    today = datetime.now(timezone.utc).strftime("%Y년 %m월 %d일")

    combined = f"""주간 리포트 — {today} 기준

■ 백엔드 (GF_Backend) - 주간
{backend_summary}

■ 프론트엔드 (GF_Frontend) - 주간
{frontend_summary}

■ 기획 (mintlify-docs) - 주간
{planning_summary}

■ 팀 진행상황 (주간)
{team_summary}

■ 미완료 TODO
{todo_section}
"""

    instruction = "다음 주간 리포트를 종합 정리해주세요. 주요 성과, 진행 중인 작업, 미해결 사항으로 분류해주세요."
    return llm_summarize(combined, instruction)
