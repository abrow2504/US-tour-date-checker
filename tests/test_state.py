import json
import pytest

from us_tour_checker import state


@pytest.fixture()
def fixed_datetime(monkeypatch):
    class DummyDateTime:
        @staticmethod
        def now():
            class Dummy:
                def isoformat(self):
                    return "2024-01-01T12:00:00"
            return Dummy()

    monkeypatch.setattr(state, "datetime", DummyDateTime)


def test_load_seen_dates_returns_empty_when_file_absent(tmp_path):
    state_path = tmp_path / "state.json"

    assert state.load_seen_dates(str(state_path)) == []


def test_load_seen_dates_reads_existing_state(tmp_path):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"dates": ["2024-06-01_city_venue_address_link"]}), encoding="utf-8")

    result = state.load_seen_dates(str(state_path))

    assert result == ["2024-06-01_city_venue_address_link"]


def test_save_seen_dates_writes_dates_and_timestamp(tmp_path, fixed_datetime):
    state_path = tmp_path / "state.json"
    dates = ["2025-04-10_city_venue_address_link"]

    state.save_seen_dates(dates, str(state_path))

    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["dates"] == dates
    assert data["last_updated"] == "2024-01-01T12:00:00"


def test_save_all_events_merges_existing_data(tmp_path, fixed_datetime):
    state_path = tmp_path / "state.json"
    initial = {"dates": ["old"], "metadata": {"version": 1}}
    state_path.write_text(json.dumps(initial), encoding="utf-8")
    events = [{"date": "2025-07-04", "city": "Austin", "venue": "ACL", "address": "Austin, TX"}]

    state.save_all_events(events, str(state_path))

    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["dates"] == initial["dates"]
    assert data["metadata"] == initial["metadata"]
    assert data["all_events"] == events
    assert data["last_scan"] == "2024-01-01T12:00:00"
