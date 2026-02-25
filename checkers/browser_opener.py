import webbrowser


def get_sites(config: dict) -> list:
    sites = config.get("browser_sites", [])
    return [s for s in sites if s.get("url")]


def open_all(config: dict) -> list:
    sites = get_sites(config)
    opened = []
    for site in sites:
        webbrowser.open(site["url"])
        opened.append(site["name"])
    return opened
