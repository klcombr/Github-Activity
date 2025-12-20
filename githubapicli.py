#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime


def fetch_events(username):
    url = f"https://api.github.com/users/{username}/events"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "github-activity-cli",
            "Accept": "application/vnd.github+json"
        }
    )

    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def format_event(event):
    event_type = event.get("type")
    repo = event.get("repo", {}).get("name", "unknown repo")
    payload = event.get("payload", {})

    # data do evento
    created_at = event.get("created_at")
    prefix = ""
    if created_at:
        date = datetime.fromisoformat(created_at.replace("Z", ""))
        prefix = f"[{date.strftime('%Y-%m-%d')}] "

    if event_type == "PushEvent":
        commits = payload.get("size", 0)
        ref = payload.get("ref", "")

        if commits > 0:
            return f"{prefix}Pushed {commits} commits to {repo}"
        elif ref.startswith("refs/tags/"):
            tag = ref.replace("refs/tags/", "")
            return f"{prefix}Pushed tag {tag} to {repo}"
        else:
            return f"{prefix}Pushed changes to {repo}"

    elif event_type == "IssuesEvent":
        action = payload.get("action")
        if action:
            return f"{prefix}{action.capitalize()} an issue in {repo}"
        return f"{prefix}Issue activity in {repo}"

    elif event_type == "WatchEvent":
        return f"{prefix}Starred {repo}"

    elif event_type == "ForkEvent":
        return f"{prefix}Forked {repo}"

    return None  


def main():
    if len(sys.argv) < 2:
        print("Uso correto: github-activity <username>")
        sys.exit(1)

    username = sys.argv[1]

    try:
        events = fetch_events(username)

        if not events:
            print("Nenhuma atividade recente encontrada.")
            return

        seen = set()
        count = 0

        for event in events:
            formatted = format_event(event)

            if formatted and formatted not in seen:
                print(f"- {formatted}")
                seen.add(formatted)
                count += 1

            if count == 10:
                break

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("Usuário não encontrado.")
        elif e.code == 403:
            print("Rate limit da API do GitHub atingido.")
        else:
            print("Erro ao acessar a API do GitHub.")

    except Exception as e:
        print("Erro inesperado:", e)


if __name__ == "__main__":
    main()
