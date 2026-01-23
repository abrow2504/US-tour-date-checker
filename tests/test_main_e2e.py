import json

from us_tour_checker import main as main_module


def test_main_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    debug_file = tmp_path / "debug_capture.html"

    config = {
        "site": {"name": "Test Artist", "url": "https://example.com"},
        "scraping": {
            "wait_for_element": ".event-card",
            "wait_timeout": 5,
            "selectors": {"event_cards": ".event-card"},
        },
        "notifications": {"email": {"subject_prefix": "New", "subject_suffix": "Dates"}},
        "debug_html_file": str(debug_file),
    }

    events = [
        {
            "date": "2026-05-01",
            "city": "Los Angeles",
            "venue": "Hollywood Bowl",
            "address": "Los Angeles, CA",
            "link": "https://tickets.test/la",
        },
        {
            "date": "2026-06-10",
            "city": "Chicago",
            "venue": "United Center",
            "address": "Chicago, IL",
            "link": "https://tickets.test/chicago",
        },
    ]

    monkeypatch.setattr(main_module, "load_config", lambda: config)

    html_content = "<html>stub</html>"

    def fake_fetch(url, wait_for_element, wait_timeout):
        assert url == config["site"]["url"]
        assert wait_for_element == config["scraping"]["wait_for_element"]
        assert wait_timeout == config["scraping"]["wait_timeout"]
        return html_content

    monkeypatch.setattr(main_module, "fetch_website", fake_fetch)

    def fake_extract(html, selectors):
        assert html == html_content
        assert selectors == config["scraping"]["selectors"]
        return events

    monkeypatch.setattr(main_module, "extract_all_events", fake_extract)

    email_calls = []
    telegram_calls = []

    def fake_email(new_dates, cfg):
        email_calls.append((list(new_dates), cfg))

    def fake_telegram(new_dates, cfg):
        telegram_calls.append((list(new_dates), cfg))

    monkeypatch.setattr(main_module, "send_email_notification", fake_email)
    monkeypatch.setattr(main_module, "send_telegram_notification", fake_telegram)

    main_module.main()

    assert debug_file.read_text(encoding="utf-8") == html_content

    seen_path = tmp_path / "seen_dates.json"
    data = json.loads(seen_path.read_text(encoding="utf-8"))
    assert set(data["dates"]) == {main_module._event_key(evt) for evt in events}
    assert email_calls and email_calls[0][0] == events
    assert telegram_calls and telegram_calls[0][0] == events
