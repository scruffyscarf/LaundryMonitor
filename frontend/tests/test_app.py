from datetime import UTC, datetime

import frontend.src.app as app
from frontend.src.models import Machine


class _DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeSidebar:
    def __init__(self):
        self._submit = True

    def header(self, *_args, **_kwargs):
        pass

    def selectbox(self, _label, options):
        return options[0] if options else ""

    def radio(self, _label, options, format_func=None):
        return options[0]

    def number_input(self, *_args, **_kwargs):
        return 0

    def text_input(self, *_args, **_kwargs):
        return ""

    def button(self, label):
        return label == "Submit"

    def error(self, *_args, **_kwargs):
        pass

    def success(self, *_args, **_kwargs):
        pass


class _FakeStreamlit:
    def __init__(self):
        self.sidebar = _FakeSidebar()
        self.session_state = {}

    def set_page_config(self, *_args, **_kwargs):
        pass

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_DummyCtx() for _ in range(count)]

    def title(self, *_args, **_kwargs):
        pass

    def button(self, *_args, **_kwargs):
        return False

    def checkbox(self, *_args, **_kwargs):
        return False

    def error(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def pills(self, *_args, **kwargs):
        return kwargs.get("default")


def test_main_runs_and_submits_report(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(app, "st", fake_st)

    machines = [
        Machine(
            id=1,
            name="Washer 1",
            type="Wash",
            status="Free",
            time_remaining=None,
            last_report_timestamp=datetime.now(UTC),
        )
    ]

    def _fake_get_machines():
        return machines, False

    called = {"post": False}

    def _fake_post_report(*_args, **_kwargs):
        called["post"] = True
        return {"ok": True}

    monkeypatch.setattr(app.api, "get_machines", _fake_get_machines)
    monkeypatch.setattr(app.api, "post_report", _fake_post_report)
    monkeypatch.setattr(app.ui, "card", lambda *_args, **_kwargs: None)

    app.main()
    assert called["post"] is True
