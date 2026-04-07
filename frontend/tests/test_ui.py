from datetime import UTC, datetime

import frontend.src.ui as ui
from frontend.src.models import Machine


class _FakeStreamlit:
    def __init__(self):
        self.last_markdown = None

    def markdown(self, html, unsafe_allow_html=False):
        self.last_markdown = (html, unsafe_allow_html)


def test_status_color_mapping():
    assert ui._status_color("Free") == "#16a34a"
    assert ui._status_color("busy") == "#dc2626"
    assert ui._status_color("Probably_Free") == "#f59e0b"
    assert ui._status_color("unavailable") == "#6b7280"


def test_card_renders_basic_fields(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(ui, "st", fake_st)

    m = Machine(
        id=1,
        name="Washer 1",
        type="Wash",
        status="Busy",
        time_remaining=20,
        last_report_timestamp=datetime.now(UTC),
    )

    ui.card(m)
    html, unsafe = fake_st.last_markdown
    assert unsafe is True
    assert "Washer 1" in html
    assert "Busy" in html
