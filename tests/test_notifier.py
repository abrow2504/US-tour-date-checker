import pytest

from us_tour_checker import notifier


@pytest.fixture(autouse=True)
def clear_notification_env(monkeypatch):
    for var in [
        "EMAIL_ADDRESS",
        "EMAIL_PASSWORD",
        "RECIPIENT_EMAIL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]:
        monkeypatch.delenv(var, raising=False)


def test_send_email_notification_skips_when_env_missing(monkeypatch, capsys):
    smtp_called = {"used": False}

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            smtp_called["used"] = True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def login(self, *args, **kwargs):
            raise AssertionError("login should not run when env vars missing")

        def sendmail(self, *args, **kwargs):
            raise AssertionError("sendmail should not run when env vars missing")

    monkeypatch.setattr(notifier.smtplib, "SMTP_SSL", DummySMTP)

    config = {"notifications": {"email": {}}, "site": {"url": "https://example.com"}}
    new_dates = [{"date": "2025-01-01", "city": "NYC", "venue": "MSG"}]

    notifier.send_email_notification(new_dates, config)

    out = capsys.readouterr().out
    assert "Email environment variables not set" in out
    assert smtp_called["used"] is False


def test_send_email_notification_sends_when_env_present(monkeypatch):
    monkeypatch.setenv("EMAIL_ADDRESS", "sender@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "password123")
    monkeypatch.setenv("RECIPIENT_EMAIL", "friend@example.com")

    smtp_context = {}

    class DummySMTP:
        def __init__(self, host, port):
            smtp_context["host"] = host
            smtp_context["port"] = port
            self.logged_in = None
            self.sent = []

        def __enter__(self):
            smtp_context["instance"] = self
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def login(self, email, password):
            self.logged_in = (email, password)

        def sendmail(self, sender, recipient, message):
            self.sent.append((sender, recipient, message))

    monkeypatch.setattr(notifier.smtplib, "SMTP_SSL", DummySMTP)

    config = {
        "notifications": {"email": {"subject_prefix": "Heads up:", "subject_suffix": "Dates"}},
        "site": {"url": "https://example.com"},
    }
    new_dates = [
        {"date": "2025-02-02", "city": "Chicago", "venue": "United Center", "link": "https://tickets/1"}
    ]

    notifier.send_email_notification(new_dates, config)

    server = smtp_context["instance"]
    assert smtp_context["host"] == "smtp.gmail.com"
    assert smtp_context["port"] == 465
    assert server.logged_in == ("sender@example.com", "password123")
    assert server.sent, "sendmail should be called"
    sent_message = server.sent[0][2]
    assert "Subject: Heads up: Dates" in sent_message
    assert "Chicago" in sent_message
    assert "https://tickets/1" in sent_message


def test_send_telegram_notification_skips_when_env_missing(monkeypatch, capsys):
    called = {"post": False}

    def fake_post(*args, **kwargs):
        called["post"] = True
        raise AssertionError("requests.post should not run without env vars")

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    notifier.send_telegram_notification([], {"site": {"url": "https://example.com"}})

    out = capsys.readouterr().out
    assert "Telegram env vars not set" in out
    assert called["post"] is False


def test_send_telegram_notification_posts_payload(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat456")

    captured = {}

    class DummyResponse:
        status_code = 200
        text = "OK"

    def fake_post(url, data, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    config = {"site": {"url": "https://fallback.com"}}
    new_dates = [
        {"date": "2025-03-03", "city": "Austin", "venue": "ACL", "link": "https://tickets/2"}
    ]

    notifier.send_telegram_notification(new_dates, config)

    assert captured["url"] == "https://api.telegram.org/bottoken123/sendMessage"
    assert captured["data"]["chat_id"] == "chat456"
    assert "Austin" in captured["data"]["text"]
    assert captured["timeout"] == 10
