from __future__ import annotations

import requests
from datetime import datetime, timezone


def check(config: dict, state: dict) -> dict | None:
    token = config.get("github", {}).get("token", "")
    repo = config.get("github", {}).get("repo", "")
    if not token or not repo:
        return None

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    base_url = f"https://api.github.com/repos/{repo}"

    # Fetch repo info
    resp = requests.get(base_url, headers=headers, timeout=10)
    resp.raise_for_status()
    repo_data = resp.json()

    stars = repo_data["stargazers_count"]
    forks = repo_data["forks_count"]

    # Fetch recent issues (open, sorted by created)
    last_checked = state.get("github", {}).get("last_checked", "")
    params = {"state": "open", "sort": "created", "direction": "desc", "per_page": 10}
    if last_checked:
        params["since"] = last_checked

    resp = requests.get(f"{base_url}/issues", headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    issues_data = resp.json()
    # Filter out pull requests
    new_issues = [i for i in issues_data if "pull_request" not in i]

    # Fetch discussions count via GraphQL (if available)
    discussions_count = 0
    try:
        owner, name = repo.split("/")
        graphql_query = {
            "query": """
            query($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                discussions { totalCount }
              }
            }
            """,
            "variables": {"owner": owner, "name": name},
        }
        resp = requests.post(
            "https://api.github.com/graphql",
            json=graphql_query,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        discussions_count = data.get("data", {}).get("repository", {}).get("discussions", {}).get("totalCount", 0)
    except Exception:
        discussions_count = None  # Discussions might be disabled

    prev = state.get("github", {})
    prev_stars = prev.get("stars", 0)
    prev_forks = prev.get("forks", 0)
    prev_discussions = prev.get("discussions", 0)
    first_run = "github" not in state

    # Format issues for display
    formatted_issues = []
    for issue in new_issues:
        created = issue["created_at"]
        age = _time_ago(created)
        formatted_issues.append({
            "number": issue["number"],
            "title": issue["title"],
            "age": age,
        })

    result = {
        "stars": stars,
        "stars_diff": stars - prev_stars,
        "forks": forks,
        "forks_diff": forks - prev_forks,
        "new_issues": formatted_issues,
        "first_run": first_run,
    }

    if discussions_count is not None:
        result["discussions"] = discussions_count
        result["discussions_diff"] = discussions_count - prev_discussions

    # Update state
    new_state = {
        "stars": stars,
        "forks": forks,
        "last_checked": datetime.now(timezone.utc).isoformat(),
    }
    if discussions_count is not None:
        new_state["discussions"] = discussions_count
    state["github"] = new_state

    return result


def _time_ago(iso_str: str) -> str:
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    diff = datetime.now(timezone.utc) - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"
