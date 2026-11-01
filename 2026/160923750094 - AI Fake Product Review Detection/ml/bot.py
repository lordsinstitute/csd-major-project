


def user_trust_score(behavior_risk, avg_fake_prob):
    """Both inputs are from 0 to 1. Returns a score from 0 to 100."""
    risk = 0.5 * behavior_risk + 0.5 * avg_fake_prob
    return round(100 * (1 - risk))


def bot_status(score):
    if score >= 70:
        return "Looks human"
    if score >= 40:
        return "Suspicious"
    return "Bot-like"
