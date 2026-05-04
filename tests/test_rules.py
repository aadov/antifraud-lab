from app.rules import make_decision


def test_make_decision_allows_low_risk_score():
    assert make_decision(0) == "ALLOW"
    assert make_decision(39) == "ALLOW"


def test_make_decision_requires_2fa_for_medium_risk_score():
    assert make_decision(40) == "2FA"
    assert make_decision(69) == "2FA"


def test_make_decision_blocks_high_risk_score():
    assert make_decision(70) == "BLOCK"
    assert make_decision(100) == "BLOCK"


from app import rules


def test_calculate_risk_scores_basic_signals_without_history(monkeypatch):
    monkeypatch.setattr(rules, "get_user_history", lambda user_id, minutes=10: [])

    event = {
        "user_id": "client_001",
        "ip": "185.22.10.11",
        "country": "RU",
        "device": "new",
        "hour": 3,
        "failed_attempts": 4,
    }

    score, reasons = rules.calculate_risk(event)

    assert score == 95
    assert reasons == [
        "new_device",
        "night_login",
        "many_failed_attempts",
        "foreign_country",
    ]


def test_calculate_risk_scores_context_rules(monkeypatch):
    fake_history = [
        ("10.0.0.1", "KZ", "old", 1),
        ("10.0.0.2", "KZ", "old", 2),
        ("10.0.0.3", "KZ", "old", 3),
        ("10.0.0.4", "KZ", "old", 4),
        ("10.0.0.5", "KZ", "old", 1),
        ("10.0.0.6", "KZ", "old", 1),
        ("10.0.0.7", "KZ", "old", 1),
        ("10.0.0.8", "KZ", "old", 1),
        ("10.0.0.9", "KZ", "old", 1),
        ("10.0.0.10", "KZ", "old", 1),
        ("10.0.0.11", "KZ", "old", 1),
        ("10.0.0.12", "KZ", "old", 1),
        ("10.0.0.13", "KZ", "old", 1),
        ("10.0.0.14", "KZ", "old", 1),
        ("10.0.0.15", "KZ", "old", 1),
        ("10.0.0.16", "KZ", "old", 1),
    ]

    monkeypatch.setattr(rules, "get_user_history", lambda user_id, minutes=10: fake_history)

    event = {
        "user_id": "client_001",
        "ip": "185.22.10.11",
        "country": "RU",
        "device": "old",
        "hour": 12,
        "failed_attempts": 0,
    }

    score, reasons = rules.calculate_risk(event)

    assert score == 165
    assert reasons == [
        "foreign_country",
        "impossible_travel",
        "multiple_ips",
        "accumulated_failed_attempts",
        "bruteforce_detected",
    ]

