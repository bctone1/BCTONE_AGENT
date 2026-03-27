import os
from datetime import datetime, timedelta, timezone
from github import Github
from dotenv import load_dotenv

load_dotenv()

_github: Github | None = None
_repos: dict = {}


def _get_github() -> Github:
    global _github
    if _github is None:
        _github = Github(os.getenv("GITHUB_TOKEN", ""))
    return _github


REPO_ENV_MAP = {
    "backend": "GITHUB_REPO_BACKEND",
    "frontend": "GITHUB_REPO_FRONTEND",
    "planning": "GITHUB_REPO_PLANNING",
}


def get_repo(repo_key: str):
    """Get repo by key: 'backend', 'frontend', or 'planning'."""
    if repo_key not in _repos:
        g = _get_github()
        env_key = REPO_ENV_MAP.get(repo_key, "")
        repo_name = os.getenv(env_key, "")
        _repos[repo_key] = g.get_repo(repo_name)
    return _repos[repo_key]


def get_recent_prs(repo_key: str, state: str = "all", limit: int = 10) -> list[dict]:
    """Get recent PRs from a repo."""
    repo = get_repo(repo_key)
    branch = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
    prs = repo.get_pulls(state=state, sort="updated", direction="desc", base=branch)

    results = []
    for pr in prs[:limit]:
        results.append({
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "merged": pr.merged,
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "url": pr.html_url,
        })
    return results


def get_recent_commits(repo_key: str, days: int = 1, limit: int = 20) -> list[dict]:
    """Get recent commits from a repo."""
    repo = get_repo(repo_key)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    branch = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
    commits = repo.get_commits(sha=branch, since=since)

    results = []
    for c in commits[:limit]:
        results.append({
            "sha": c.sha[:7],
            "message": c.commit.message,
            "author": c.commit.author.name,
            "date": c.commit.author.date.isoformat(),
        })
    return results


def get_pr_diff(repo_key: str, pr_number: int) -> dict:
    """Get diff details for a specific PR."""
    repo = get_repo(repo_key)
    pr = repo.get_pull(pr_number)
    files = pr.get_files()

    return {
        "number": pr.number,
        "title": pr.title,
        "files": [
            {
                "filename": f.filename,
                "additions": f.additions,
                "deletions": f.deletions,
                "patch": f.patch[:500] if f.patch else "",
            }
            for f in files
        ],
    }
