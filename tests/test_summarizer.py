import pytest
from unittest.mock import patch, MagicMock


def test_summarize_github_changes():
    mock_prs = [
        {"number": 42, "title": "feat: login API", "state": "closed", "merged": True, "author": "damien", "url": "https://..."},
        {"number": 43, "title": "fix: token refresh", "state": "open", "merged": False, "author": "damien", "url": "https://..."},
    ]
    mock_commits = [
        {"sha": "abc1234", "message": "feat: add login", "author": "damien", "date": "2026-03-27"},
    ]

    with patch("bctone.services.summarizer.get_recent_prs", return_value=mock_prs):
        with patch("bctone.services.summarizer.get_recent_commits", return_value=mock_commits):
            with patch("bctone.services.summarizer.llm_summarize", return_value="백엔드: PR #42 머지, #43 리뷰 대기"):
                from bctone.services.summarizer import summarize_github
                result = summarize_github("backend")

    assert "백엔드" in result


def test_summarize_team_progress():
    mock_memories = [
        {"category": "progress", "content": "로그인 구현 완료", "summary": "백엔드 로그인 완료", "source_user": "U1"},
        {"category": "decision", "content": "JWT 방식 확정", "summary": "JWT 확정", "source_user": "U2"},
    ]

    with patch("bctone.services.summarizer.get_recent_memories", return_value=mock_memories):
        with patch("bctone.services.summarizer.llm_summarize", return_value="팀 진행: 로그인 완료, JWT 확정"):
            from bctone.services.summarizer import summarize_team_progress
            result = summarize_team_progress()

    assert "팀 진행" in result


def test_generate_daily_report():
    with patch("bctone.services.summarizer.summarize_github", side_effect=["백엔드 요약", "프론트 요약", "기획 요약"]):
        with patch("bctone.services.summarizer.summarize_team_progress", return_value="팀 진행 요약"):
            with patch("bctone.services.summarizer.get_todos", return_value=[]):
                with patch("bctone.services.summarizer.llm_summarize", return_value="일일 리포트 전체 요약"):
                    from bctone.services.summarizer import generate_daily_report
                    result = generate_daily_report()

    assert "일일 리포트" in result
