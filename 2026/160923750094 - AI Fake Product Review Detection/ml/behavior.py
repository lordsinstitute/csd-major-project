
def behavior_risk(reviews_last_24h, account_age_days):
    """Returns (risk from 0 to 1, list of reasons)."""
    reasons = []

    if reviews_last_24h >= 10:
        post_risk = 1.0
        reasons.append(f"{reviews_last_24h} reviews in one day (very high).")
    elif reviews_last_24h >= 5:
        post_risk = 0.6
        reasons.append(f"{reviews_last_24h} reviews in one day (high).")
    elif reviews_last_24h >= 3:
        post_risk = 0.3
        reasons.append(f"{reviews_last_24h} reviews in one day (a little high).")
    else:
        post_risk = 0.0

    if account_age_days < 1:
        age_risk = 0.5
        reasons.append("Account was created today.")
    elif account_age_days < 7:
        age_risk = 0.3
        reasons.append(f"Account is only {account_age_days} days old.")
    else:
        age_risk = 0.0

    return max(post_risk, age_risk), reasons
