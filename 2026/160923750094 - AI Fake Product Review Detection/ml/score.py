# STEP 6: Mix text and behaviour into one trust score from 0 to 100.


def trust_score(fake_prob, behavior_risk=None):
    """fake_prob: 0 to 1 from the text model. behavior_risk: 0 to 1, or None if unknown."""
    if behavior_risk is None:                       # no user info: text only
        risk = fake_prob
    else:
        risk = 0.7 * fake_prob + 0.3 * behavior_risk    # text counts more
    return round(100 * (1 - risk))


def level_name(score):
    if score >= 70:
        return "Trusted"
    if score >= 40:
        return "Needs a check"
    return "Likely fake or bot"
