# STEP 5: Bot detection and the USER trust score.
# A user is judged by two things, mixed 50/50:
#   1. behaviour risk (many reviews in a day, very new account)
#   2. average fake chance of the reviews this user wrote (from the text model)


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
