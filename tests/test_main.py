import json
from unittest.mock import patch, MagicMock

import urllib.request
import urllib.error

import main


def make_event(event_type, repo="user/repo", payload=None, created_at="2026-08-01T10:00:00Z"):
    return {
        "type": event_type,
        "repo": {"name": repo},
        "payload": payload or {},
        "created_at": created_at,
    }


def test_format_push_event():
    event = make_event("PushEvent", payload={"size": 3, "ref": "refs/heads/main"})
    assert "Enviou 3 commits para user/repo" in main.format_event(event)


def test_format_push_tag_event():
    event = make_event("PushEvent", payload={"size": 0, "ref": "refs/tags/v1.0"})
    assert "tag v1.0" in main.format_event(event)


def test_format_issues_event():
    event = make_event("IssuesEvent", payload={"action": "opened"})
    assert "Opened uma issue em user/repo" in main.format_event(event)


def test_format_watch_event():
    assert main.format_event(make_event("WatchEvent")) == "[2026-08-01] Deu estrela em user/repo"


def test_format_fork_event():
    assert "Forkou" in main.format_event(make_event("ForkEvent"))


def test_format_create_event():
    event = make_event("CreateEvent", payload={"ref_type": "branch", "ref": "feat/x"})
    assert "Criou a branch feat/x em user/repo" in main.format_event(event)


def test_format_pull_request_event():
    event = make_event("PullRequestEvent", payload={"action": "opened", "number": 5, "pull_request": {"title": "Fix bug"}})
    assert "pull request 'Fix bug'" in main.format_event(event)


def test_format_issue_comment_event():
    event = make_event("IssueCommentEvent", payload={"action": "created"})
    assert "Comentou em uma issue" in main.format_event(event)


def test_format_release_event():
    event = make_event("ReleaseEvent", payload={"action": "published", "release": {"tag_name": "v1.0"}})
    assert "release v1.0" in main.format_event(event)


def test_format_delete_event():
    event = make_event("DeleteEvent", payload={"ref_type": "branch", "ref": "old-branch"})
    assert "Excluiu o branch old-branch" in main.format_event(event)


def test_format_unknown_event():
    event = make_event("MysteryEvent", payload={})
    assert "Evento MysteryEvent em user/repo" in main.format_event(event)


def make_response(body, status=200):
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode()
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


def test_fetch_events_returns_list():
    body = [{"type": "WatchEvent", "repo": {"name": "a/b"}, "payload": {}, "created_at": None}]
    with patch("main.urllib.request.urlopen", return_value=make_response(body)) as mock_urlopen:
        events = main.fetch_events("octocat")
    assert events == body
    req = mock_urlopen.call_args[0][0]
    assert isinstance(req, urllib.request.Request)
    assert "user-agent" in [h.lower() for h, _ in req.header_items()]


def test_fetch_events_uses_token():
    body = []
    with patch("main.urllib.request.urlopen", return_value=make_response(body)) as mock_urlopen:
        with patch.dict("main.os.environ", {"GITHUB_TOKEN": "secret"}, clear=True):
            main.fetch_events("octocat")
    req = mock_urlopen.call_args[0][0]
    headers = dict(req.header_items())
    assert headers.get("Authorization") == "Bearer secret"


def test_fetch_events_dict_response_raises():
    body = {"message": "API rate limit exceeded", "documentation_url": "x"}
    with patch("main.urllib.request.urlopen", return_value=make_response(body)):
        try:
            main.fetch_events("octocat")
            assert False, "deveria levantar exceção para resposta em dict"
        except ValueError:
            pass


def test_fetch_events_404():
    error = urllib.error.HTTPError("url", 404, "Not Found", None, None)
    with patch("main.urllib.request.urlopen", side_effect=error):
        try:
            main.fetch_events("nao-existe")
            assert False, "deveria propagar HTTPError 404"
        except urllib.error.HTTPError as e:
            assert e.code == 404


def test_fetch_events_403():
    error = urllib.error.HTTPError("url", 403, "Forbidden", None, None)
    with patch("main.urllib.request.urlopen", side_effect=error):
        try:
            main.fetch_events("octocat")
            assert False, "deveria propagar HTTPError 403"
        except urllib.error.HTTPError as e:
            assert e.code == 403
