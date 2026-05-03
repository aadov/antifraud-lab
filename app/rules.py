from app.db import get_user_history

def calculate_risk(event):
    score = 0
    reasons = []

    if event["device"] == "new":
        score += 30
        reasons.append("new_device")

    if event["hour"] < 6 or event["hour"] > 23:
        score += 20
        reasons.append("night_login")

    if event["failed_attempts"] > 3:
        score += 25
        reasons.append("many_failed_attempts")

    if event["country"] != "KZ":
        score += 20
        reasons.append("foreign_country")

    history = get_user_history(event["user_id"], minutes=10)

    if history:
        countries = [row[1] for row in history]
        ips = [row[0] for row in history]
        failed_sum = sum(row[3] for row in history)

        if event["country"] != "KZ" and "KZ" in countries:
            score += 40
            reasons.append("impossible_travel")

        unique_ips = set(ips)
        if len(unique_ips) >= 3:
            score += 30
            reasons.append("multiple_ips")

        if failed_sum > 10:
            score += 35
            reasons.append("accumulated_failed_attempts")

        if len(history) > 15:
            score += 40
            reasons.append("bruteforce_detected")

    return score, reasons


def make_decision(score):
    if score >= 70:
        return "BLOCK"
    elif score >= 40:
        return "2FA"
    else:
        return "ALLOW"
