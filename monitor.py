#!/usr/bin/env python3
"""AWT Launch Monitor - Track your launch across multiple platforms."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from checkers import github_checker, devto_checker, hashnode_checker, browser_opener, telegram_notifier

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
CONFIG_EXAMPLE_PATH = BASE_DIR / "config.example.json"
STATE_PATH = BASE_DIR / "state.json"

console = Console()


def load_config() -> dict | None:
    if not CONFIG_PATH.exists():
        console.print(
            f"[bold red]config.json not found![/]\n"
            f"Copy the example and fill in your tokens:\n"
            f"  cp {CONFIG_EXAMPLE_PATH} {CONFIG_PATH}",
        )
        return None
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


def _diff_str(diff: int) -> str:
    if diff > 0:
        return f"[green](+{diff})[/]"
    if diff == 0:
        return "[dim](no change)[/]"
    return f"[red]({diff})[/]"


def print_header():
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = Text(f"AWT Launch Monitor - {today}", style="bold white", justify="center")
    console.print(Panel(header, style="bright_blue"))
    console.print()


def print_github(result: dict, config: dict, summary: bool = False):
    repo = config.get("github", {}).get("repo", "")
    if result.get("first_run"):
        console.print(f"[yellow]  First run - baseline saved[/]")

    console.print(f"[bold yellow]:star: GitHub: {repo}[/]")
    console.print(f"   Stars: {result['stars']} {_diff_str(result['stars_diff'])}")

    if not summary and result["new_issues"]:
        console.print(f"   Issues: [bold]{len(result['new_issues'])} new[/]")
        for issue in result["new_issues"]:
            console.print(f'     → [cyan]#{issue["number"]}[/]: "{issue["title"]}" ({issue["age"]})')
    else:
        console.print(f"   Issues: 0 new")

    if "discussions" in result:
        console.print(f"   Discussions: {result['discussions']} {_diff_str(result['discussions_diff'])}")

    console.print(f"   Forks: {result['forks']} {_diff_str(result['forks_diff'])}")
    console.print()


def print_devto(results: list, summary: bool = False):
    if not results:
        console.print("[dim]  DEV.to: No changes since last check[/]")
        console.print()
        return

    for r in results:
        if r.get("first_run"):
            console.print(f"[yellow]  First run - baseline saved[/]")

        console.print(f'[bold magenta]:memo: DEV.to: "{r["title"]}"[/]')
        console.print(f"   Views: {r['views']} {_diff_str(r['views_diff'])}")
        console.print(f"   Reactions: {r['reactions']} {_diff_str(r['reactions_diff'])}")

        if summary:
            console.print(f"   Comments: {r['new_comment_count']} new")
        else:
            console.print(f"   Comments: {r['new_comment_count']} new")
            for c in r.get("new_comments", []):
                console.print(f'     → [cyan]@{c["username"]}[/]: "{c["preview"]}" ({c["age"]})')

        console.print()


def print_hashnode(results: list, summary: bool = False):
    if not results:
        console.print("[dim]  Hashnode: No changes since last check[/]")
        console.print()
        return

    for r in results:
        if r.get("first_run"):
            console.print(f"[yellow]  First run - baseline saved[/]")

        console.print(f'[bold magenta]:memo: Hashnode: "{r["title"]}"[/]')
        console.print(f"   Reactions: {r['reactions']} {_diff_str(r['reactions_diff'])}")

        if summary:
            console.print(f"   Comments: {r['new_comment_count']} new")
        else:
            console.print(f"   Comments: {r['new_comment_count']} new")
            for c in r.get("new_comments", []):
                console.print(f'     → [cyan]@{c["username"]}[/]: "{c["preview"]}" ({c["age"]})')

        console.print()


def print_browser_sites(config: dict):
    sites = browser_opener.get_sites(config)
    if not sites:
        return
    names = ", ".join(s["name"] for s in sites)
    console.print(f"[bold blue]:globe_with_meridians: Browser Check Needed:[/]")
    console.print(f"   → {names}")
    console.print(f"   Run [bold]python monitor.py --open-browsers[/] to open all")
    console.print()


def run_github(config: dict, state: dict, summary: bool = False, silent: bool = False) -> dict | None:
    try:
        result = github_checker.check(config, state)
        if result is None:
            if not silent:
                console.print("[dim]  GitHub: Skipped (no token configured)[/]")
                console.print()
            return None
        if not silent:
            print_github(result, config, summary)
        return result
    except Exception as e:
        if not silent:
            console.print(f"[red]  GitHub: Error - {e}[/]")
            console.print()
        return None


def run_devto(config: dict, state: dict, summary: bool = False, silent: bool = False) -> list | None:
    try:
        results = devto_checker.check(config, state)
        if results is None:
            if not silent:
                console.print("[dim]  DEV.to: Skipped (no API key configured)[/]")
                console.print()
            return None
        if not silent:
            print_devto(results, summary)
        return results
    except Exception as e:
        if not silent:
            console.print(f"[red]  DEV.to: Error - {e}[/]")
            console.print()
        return None


def run_hashnode(config: dict, state: dict, summary: bool = False, silent: bool = False) -> list | None:
    try:
        results = hashnode_checker.check(config, state)
        if results is None:
            if not silent:
                console.print("[dim]  Hashnode: Skipped (no token configured)[/]")
                console.print()
            return None
        if not silent:
            print_hashnode(results, summary)
        return results
    except Exception as e:
        if not silent:
            console.print(f"[red]  Hashnode: Error - {e}[/]")
            console.print()
        return None


def main():
    parser = argparse.ArgumentParser(description="AWT Launch Monitor")
    parser.add_argument("--github", action="store_true", help="Check GitHub only")
    parser.add_argument("--devto", action="store_true", help="Check DEV.to only")
    parser.add_argument("--hashnode", action="store_true", help="Check Hashnode only")
    parser.add_argument("--open-browsers", action="store_true", help="Open browser-only sites")
    parser.add_argument("--summary", action="store_true", help="Show summary only (no comment previews)")
    parser.add_argument("--notify", action="store_true", help="Terminal output + Telegram notification")
    parser.add_argument("--silent", action="store_true", help="Telegram only, no terminal output (for cron)")
    args = parser.parse_args()

    config = load_config()
    if config is None:
        sys.exit(1)

    state = load_state()
    silent = args.silent
    send_telegram = args.notify or args.silent

    if not silent:
        print_header()

    # If --open-browsers, just open and exit
    if args.open_browsers:
        opened = browser_opener.open_all(config)
        if opened:
            console.print(f"[green]Opened: {', '.join(opened)}[/]")
        else:
            console.print("[yellow]No browser sites configured with URLs.[/]")
        save_state(state)
        return

    # Specific platform or all
    specific = args.github or args.devto or args.hashnode
    summary = args.summary

    # Collect results for telegram
    telegram_sections = []

    if not specific or args.github:
        gh_result = run_github(config, state, summary, silent)
        if gh_result and send_telegram:
            telegram_sections.append(telegram_notifier.format_github(gh_result, config))

    if not specific or args.devto:
        devto_results = run_devto(config, state, summary, silent)
        if send_telegram:
            telegram_sections.append(telegram_notifier.format_devto(devto_results or []))

    if not specific or args.hashnode:
        hn_results = run_hashnode(config, state, summary, silent)
        if send_telegram:
            telegram_sections.append(telegram_notifier.format_hashnode(hn_results or []))

    if not specific:
        if not silent:
            print_browser_sites(config)
        if send_telegram:
            browser_text = telegram_notifier.format_browser_sites(config)
            if browser_text:
                telegram_sections.append(browser_text)

    # Send telegram notification
    if send_telegram and telegram_sections:
        message = telegram_notifier.build_message(telegram_sections)
        try:
            telegram_notifier.send(config, message)
            if not silent:
                console.print("[green]Telegram notification sent.[/]")
        except Exception as e:
            if not silent:
                console.print(f"[red]Telegram: Error - {e}[/]")
            else:
                print(f"Telegram error: {e}", file=sys.stderr)

    save_state(state)


if __name__ == "__main__":
    main()
