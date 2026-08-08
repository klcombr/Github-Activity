#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any


def fetch_events(username: str) -> list[dict]:
    url = f"https://api.github.com/users/{username}/events"

    headers = {
        "User-Agent": "github-activity-cli",
        "Accept": "application/vnd.github+json"
    }

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read())

    if not isinstance(data, list):
        raise ValueError("A API do GitHub retornou uma resposta inesperada.")

    return data


def format_event(event: dict) -> str | None:
    event_type = event.get("type")
    repo = event.get("repo", {}).get("name", "repositório desconhecido")
    payload = event.get("payload", {})

    created_at = event.get("created_at")
    prefix = ""
    if created_at:
        date = datetime.fromisoformat(created_at.replace("Z", ""))
        prefix = f"[{date.strftime('%Y-%m-%d')}] "

    if event_type == "PushEvent":
        commits = payload.get("size", 0)
        ref = payload.get("ref", "")

        if commits > 0:
            return f"{prefix}Enviou {commits} commits para {repo}"
        elif ref.startswith("refs/tags/"):
            tag = ref.replace("refs/tags/", "")
            return f"{prefix}Enviou a tag {tag} para {repo}"
        else:
            return f"{prefix}Enviou alterações para {repo}"

    elif event_type == "IssuesEvent":
        action = payload.get("action")
        if action:
            return f"{prefix}{action.capitalize()} uma issue em {repo}"
        return f"{prefix}Atividade de issue em {repo}"

    elif event_type == "WatchEvent":
        return f"{prefix}Deu estrela em {repo}"

    elif event_type == "ForkEvent":
        return f"{prefix}Forkou {repo}"

    elif event_type == "CreateEvent":
        ref_type = payload.get("ref_type", "")
        ref = payload.get("ref", "")
        if ref_type == "branch" and ref:
            return f"{prefix}Criou a branch {ref} em {repo}"
        elif ref_type and ref:
            return f"{prefix}Criou o {ref_type} {ref} em {repo}"
        return f"{prefix}Criou um {ref_type} em {repo}"

    elif event_type == "PullRequestEvent":
        action = payload.get("action")
        pr_number = payload.get("number")
        title = payload.get("pull_request", {}).get("title")
        detail = f"'{title}'" if title else f"#{pr_number}"
        if action:
            return f"{prefix}{action.capitalize()} o pull request {detail} em {repo}"
        return f"{prefix}Atividade de pull request em {repo}"

    elif event_type == "IssueCommentEvent":
        action = payload.get("action")
        return f"{prefix}Comentou em uma issue em {repo} ({action})"

    elif event_type == "ReleaseEvent":
        action = payload.get("action")
        release_name = payload.get("release", {}).get("name") or payload.get("release", {}).get("tag_name")
        detail = f" {release_name}" if release_name else ""
        return f"{prefix}Publicou a release{detail} em {repo} ({action})"

    elif event_type == "DeleteEvent":
        ref_type = payload.get("ref_type", "")
        ref = payload.get("ref", "")
        detail = f" {ref}" if ref else ""
        return f"{prefix}Excluiu o {ref_type}{detail} em {repo}"

    elif event_type == "PullRequestReviewEvent":
        action = payload.get("action")
        return f"{prefix}Revisou um pull request em {repo} ({action})"

    elif event_type == "PullRequestReviewCommentEvent":
        return f"{prefix}Comentou na revisão de um pull request em {repo}"

    elif event_type == "PublicEvent":
        return f"{prefix}Tornou {repo} público"

    elif event_type == "MemberEvent":
        action = payload.get("action")
        return f"{prefix}Adicionou um colaborador em {repo} ({action})"

    elif event_type == "GollumEvent":
        return f"{prefix}Atualizou a wiki de {repo}"

    if event_type:
        return f"{prefix}Evento {event_type} em {repo}"

    return None


def main() -> None:
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
            print(f"Erro ao acessar a API do GitHub (código {e.code}).")

    except Exception as e:
        print("Erro inesperado:", e)


if __name__ == "__main__":
    main()
