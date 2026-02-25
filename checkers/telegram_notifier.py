from __future__ import annotations

import requests
from datetime import datetime


def _diff_str(diff: int) -> str:
    if diff > 0:
        return f"🔺+{diff}"
    if diff == 0:
        return "변화 없음"
    return f"🔻{diff}"


def format_github(result: dict, config: dict) -> str:
    repo = config.get("github", {}).get("repo", "")
    lines = [f"⭐ GitHub: {repo}"]

    if result.get("first_run"):
        lines.append("  (첫 실행 - 기준값 저장)")

    lines.append(f"  Stars: {result['stars']} ({_diff_str(result['stars_diff'])})")

    if result["new_issues"]:
        lines.append(f"  Issues: {len(result['new_issues'])}개 새로 등록")
        for issue in result["new_issues"]:
            lines.append(f'    → #{issue["number"]}: {issue["title"]} ({issue["age"]})')
    else:
        lines.append("  Issues: 0개")

    if "discussions" in result:
        lines.append(f"  Discussions: {result['discussions']} ({_diff_str(result['discussions_diff'])})")

    lines.append(f"  Forks: {result['forks']} ({_diff_str(result['forks_diff'])})")

    return "\n".join(lines)


def format_devto(results: list) -> str:
    if not results:
        return "📝 DEV.to: 변화 없음"

    blocks = []
    for r in results:
        lines = [f'📝 DEV.to: "{r["title"]}"']
        if r.get("first_run"):
            lines.append("  (첫 실행 - 기준값 저장)")
        lines.append(f"  Views: {r['views']} ({_diff_str(r['views_diff'])})")
        lines.append(f"  Reactions: {r['reactions']} ({_diff_str(r['reactions_diff'])})")
        lines.append(f"  Comments: {r['new_comment_count']}개 새 댓글")
        for c in r.get("new_comments", []):
            lines.append(f'    → @{c["username"]}: "{c["preview"]}" ({c["age"]})')
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_hashnode(results: list) -> str:
    if not results:
        return "📝 Hashnode: 변화 없음"

    blocks = []
    for r in results:
        lines = [f'📝 Hashnode: "{r["title"]}"']
        if r.get("first_run"):
            lines.append("  (첫 실행 - 기준값 저장)")
        lines.append(f"  Reactions: {r['reactions']} ({_diff_str(r['reactions_diff'])})")
        lines.append(f"  Comments: {r['new_comment_count']}개 새 댓글")
        for c in r.get("new_comments", []):
            lines.append(f'    → @{c["username"]}: "{c["preview"]}" ({c["age"]})')
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_browser_sites(config: dict) -> str:
    from checkers import browser_opener
    sites = browser_opener.get_sites(config)
    if not sites:
        return ""
    names = ", ".join(s["name"] for s in sites)
    return f"🌐 브라우저 확인 필요: {names}"


def build_message(sections: list[str]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"📊 AWT Launch Monitor\n🕐 {now}\n{'─' * 30}"
    body = "\n\n".join(s for s in sections if s)
    return f"{header}\n\n{body}"


def send(config: dict, message: str) -> bool:
    bot_token = config.get("telegram", {}).get("bot_token", "")
    chat_id = config.get("telegram", {}).get("chat_id", "")
    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }, timeout=10)
    resp.raise_for_status()
    return True
