from __future__ import annotations

import requests
from datetime import datetime, timezone


POSTS_QUERY = """
query($host: String!) {
  publication(host: $host) {
    posts(first: 10) {
      edges {
        node {
          id
          title
          reactionCount
          comments(first: 10, sortBy: RECENT) {
            edges {
              node {
                id
                content { text }
                author { username }
                dateAdded
              }
            }
            totalDocuments
          }
        }
      }
    }
  }
}
"""


def check(config: dict, state: dict) -> list | None:
    token = config.get("hashnode", {}).get("token", "")
    host = config.get("hashnode", {}).get("publication_host", "")
    if not token or not host:
        return None

    headers = {"Authorization": token, "Content-Type": "application/json"}

    resp = requests.post(
        "https://gql.hashnode.com",
        json={"query": POSTS_QUERY, "variables": {"host": host}},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    publication = data.get("data", {}).get("publication")
    if not publication:
        return None

    posts = publication.get("posts", {}).get("edges", [])
    prev_posts = state.get("hashnode", {}).get("posts", {})
    first_run = "hashnode" not in state

    results = []
    new_state_posts = {}

    for edge in posts:
        post = edge["node"]
        post_id = post["id"]
        title = post["title"]
        reactions = post["reactionCount"]
        comments_data = post.get("comments", {})
        total_comments = comments_data.get("totalDocuments", 0)

        prev = prev_posts.get(post_id, {})
        prev_reactions = prev.get("reactions", 0)
        prev_comments = prev.get("comments_count", 0)

        new_comment_count = total_comments - prev_comments

        # Format new comments
        new_comments = []
        if new_comment_count > 0:
            comment_edges = comments_data.get("edges", [])
            for c_edge in comment_edges[:max(new_comment_count, 0)]:
                c = c_edge["node"]
                username = c.get("author", {}).get("username", "unknown")
                text = c.get("content", {}).get("text", "")[:80]
                age = _time_ago(c.get("dateAdded", ""))
                new_comments.append({
                    "username": username,
                    "preview": text,
                    "age": age,
                })

        result = {
            "title": title,
            "reactions": reactions,
            "reactions_diff": reactions - prev_reactions,
            "new_comments": new_comments,
            "new_comment_count": max(new_comment_count, 0),
            "first_run": first_run,
        }

        if first_run or reactions - prev_reactions > 0 or new_comment_count > 0:
            results.append(result)

        new_state_posts[post_id] = {
            "title": title,
            "reactions": reactions,
            "comments_count": total_comments,
        }

    state["hashnode"] = {"posts": new_state_posts}

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
