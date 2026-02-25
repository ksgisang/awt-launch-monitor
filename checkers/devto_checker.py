from __future__ import annotations

import requests
from datetime import datetime, timezone


def check(config: dict, state: dict) -> list | None:
    api_key = config.get("devto", {}).get("api_key", "")
    if not api_key:
        return None

    headers = {"api-key": api_key, "Accept": "application/json"}

    # Fetch my articles
    resp = requests.get(
        "https://dev.to/api/articles/me",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    articles = resp.json()

    prev_articles = state.get("devto", {}).get("articles", {})
    first_run = "devto" not in state

    results = []
    new_state_articles = {}

    for article in articles:
        article_id = str(article["id"])
        title = article["title"]
        views = article.get("page_views_count", 0) or 0
        reactions = article["positive_reactions_count"]
        comments_count = article["comments_count"]

        prev = prev_articles.get(article_id, {})
        prev_views = prev.get("views", 0)
        prev_reactions = prev.get("reactions", 0)
        prev_comments = prev.get("comments_count", 0)

        new_comment_count = comments_count - prev_comments

        # Fetch new comments if there are any
        new_comments = []
        if new_comment_count > 0:
            try:
                resp = requests.get(
                    f"https://dev.to/api/comments?a_id={article['id']}",
                    headers={"Accept": "application/json"},
                    timeout=10,
                )
                resp.raise_for_status()
                all_comments = resp.json()
                # Sort by created_at desc, take new ones
                all_comments.sort(
                    key=lambda c: c.get("created_at", ""), reverse=True
                )
                for c in all_comments[:max(new_comment_count, 0)]:
                    username = c.get("user", {}).get("username", "unknown")
                    body = c.get("body_html", "")
                    # Strip HTML for preview
                    import re
                    preview = re.sub(r"<[^>]+>", "", body)[:80]
                    age = _time_ago(c.get("created_at", ""))
                    new_comments.append({
                        "username": username,
                        "preview": preview,
                        "age": age,
                    })
            except Exception:
                pass

        result = {
            "title": title,
            "views": views,
            "views_diff": views - prev_views,
            "reactions": reactions,
            "reactions_diff": reactions - prev_reactions,
            "new_comments": new_comments,
            "new_comment_count": max(new_comment_count, 0),
            "first_run": first_run,
            "url": article.get("url", ""),
        }

        # Only include articles with changes or on first run
        if first_run or any([
            views - prev_views > 0,
            reactions - prev_reactions > 0,
            new_comment_count > 0,
        ]):
            results.append(result)

        new_state_articles[article_id] = {
            "title": title,
            "views": views,
            "reactions": reactions,
            "comments_count": comments_count,
        }

    state["devto"] = {"articles": new_state_articles}

    return results


def _time_ago(iso_str: str) -> str:
    try:
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
    except Exception:
        return ""
