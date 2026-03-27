import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


def _mock_pr(number, title, state, merged, user="dev1"):
    pr = MagicMock()
    pr.number = number
    pr.title = title
    pr.state = state
    pr.merged = merged
    pr.user.login = user
    pr.created_at = datetime(2026, 3, 27, tzinfo=timezone.utc)
    pr.html_url = f"https://github.com/owner/repo/pull/{number}"

    file1 = MagicMock()
    file1.filename = "src/main.py"
    file1.additions = 10
    file1.deletions = 3
    file1.patch = "@@ -1,5 +1,12 @@\n+new code here"
    pr.get_files.return_value = [file1]

    return pr


def _mock_commit(sha, message, author="dev1"):
    commit = MagicMock()
    commit.sha = sha[:7]
    commit.commit.message = message
    commit.commit.author.name = author
    commit.commit.author.date = datetime(2026, 3, 27, tzinfo=timezone.utc)
    return commit


def test_get_recent_prs():
    mock_repo = MagicMock()
    mock_repo.get_pulls.return_value = [
        _mock_pr(42, "feat: login API", "closed", True),
        _mock_pr(43, "fix: token refresh", "open", False),
    ]

    with patch("bctone.services.github_service.get_repo", return_value=mock_repo):
        from bctone.services.github_service import get_recent_prs
        prs = get_recent_prs("backend")

    assert len(prs) == 2
    assert prs[0]["number"] == 42
    assert prs[0]["merged"] is True


def test_get_recent_commits():
    mock_repo = MagicMock()
    mock_repo.get_commits.return_value = [
        _mock_commit("abc1234", "feat: add login"),
        _mock_commit("def5678", "fix: token bug"),
    ]

    with patch("bctone.services.github_service.get_repo", return_value=mock_repo):
        from bctone.services.github_service import get_recent_commits
        commits = get_recent_commits("backend", days=7)

    assert len(commits) == 2
    assert commits[0]["message"] == "feat: add login"


def test_get_pr_diff():
    mock_repo = MagicMock()
    mock_repo.get_pull.return_value = _mock_pr(42, "feat: login", "closed", True)

    with patch("bctone.services.github_service.get_repo", return_value=mock_repo):
        from bctone.services.github_service import get_pr_diff
        diff = get_pr_diff("backend", 42)

    assert len(diff["files"]) == 1
    assert diff["files"][0]["filename"] == "src/main.py"
    assert diff["files"][0]["additions"] == 10
