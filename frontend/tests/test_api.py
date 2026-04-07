from datetime import UTC, datetime

import frontend.src.api as api
from frontend.src.models import Machine


class _FakeResponse:
    def __init__(self, payload, status_ok=True):
        self._payload = payload
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise Exception("http error")

    def json(self):
        return self._payload


def test_get_machines_success(monkeypatch):
    now = datetime.now(UTC).isoformat()
    payload = [
        {
            "id": 1,
            "name": "Washer 1",
            "type": "Wash",
            "status": "Free",
            "time_remaining": None,
            "last_report_timestamp": now,
        }
    ]

    def _fake_get(url, **_kwargs):
        assert "/machines/" in url
        return _FakeResponse(payload)

    monkeypatch.setattr(api.requests, "get", _fake_get)

    machines, mocked = api.get_machines()
    assert mocked is False
    assert len(machines) == 1
    assert isinstance(machines[0], Machine)
    assert machines[0].name == "Washer 1"


def test_get_machines_fallback_to_mock(monkeypatch):
    def _fake_get(*_args, **_kwargs):
        raise Exception("boom")

    monkeypatch.setattr(api.requests, "get", _fake_get)

    machines, mocked = api.get_machines()
    assert mocked is True
    assert len(machines) >= 1


def test_post_report_success(monkeypatch):
    def _fake_post(*_args, **_kwargs):
        return _FakeResponse({"ok": True})

    monkeypatch.setattr(api.requests, "post", _fake_post)

    res = api.post_report(1, "free", time_remaining=None, reporter=None)
    assert res == {"ok": True}


def test_post_report_fallback(monkeypatch):
    def _fake_post(*_args, **_kwargs):
        raise Exception("boom")

    monkeypatch.setattr(api.requests, "post", _fake_post)

    res = api.post_report(2, "busy", time_remaining=10, reporter="a")
    assert res["mock"] is True
    assert res["machine_id"] == 2
