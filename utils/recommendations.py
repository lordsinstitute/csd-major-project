"""Disease information, recommendations and risk level rules."""

from flask import current_app

# Static, hand-written content (no text dataset is needed)
DISEASE_INFO = {
    "Healthy": {
        "title": "Healthy",
        "css": "healthy",
        "summary": (
            "The droppings in this image do not show the patterns the model "
            "associates with the three target diseases."
        ),
        "signs": [],
        "spread": "",
    },
    "Coccidiosis": {
        "title": "Coccidiosis",
        "css": "coccidiosis",
        "summary": (
            "A parasitic poultry disease (caused by Eimeria protozoa) that "
            "affects the intestines."
        ),
        "signs": [
            "Bloody or watery droppings",
            "Weakness and ruffled feathers",
            "Reduced feed intake and weight loss",
        ],
        "spread": "Spreads through contaminated litter, feed and droppings, "
        "especially when litter is damp.",
    },
    "Salmonella": {
        "title": "Salmonella",
        "css": "salmonella",
        "summary": (
            "A bacterial infection that spreads through contaminated "
            "feed and water."
        ),
        "signs": [
            "Diarrhoea and dehydration",
            "Weakness, drowsiness and poor growth",
            "Higher death rate in young chicks",
        ],
        "spread": "Spreads through contaminated feed, water, rodents and "
        "infected birds. Some types can also infect people, so wash hands "
        "after handling birds.",
    },
    "Newcastle": {
        "title": "Newcastle Disease",
        "css": "newcastle",
        "summary": (
            "A serious, highly contagious viral disease that needs urgent "
            "attention."
        ),
        "signs": [
            "Greenish watery droppings",
            "Coughing, gasping and nasal discharge",
            "Twisted neck, tremors or paralysis",
            "Sudden deaths in the flock",
        ],
        "spread": "Spreads quickly through bird contact, droppings, "
        "equipment, vehicles and people. It is a reportable disease in many "
        "countries, so follow your local veterinary authority's guidance.",
    },
}

RECOMMENDATIONS = {
    "Healthy": [
        "Continue monitoring.",
        "Maintain hygiene.",
        "Continue regular cleaning of the shed.",
    ],
    "Coccidiosis": [
        "Keep litter dry.",
        "Separate weak birds.",
        "Maintain sanitation.",
    ],
    "Salmonella": [
        "Clean feed containers.",
        "Disinfect water system.",
        "Prevent contamination.",
        "Watch for spread to other birds.",
    ],
    "Newcastle": [
        "Immediately isolate birds.",
        "Contact veterinarian.",
        "Strict biosecurity.",
    ],
}

_FALLBACK_INFO = {
    "title": "Unknown",
    "css": "healthy",
    "summary": "No information is available for this result.",
    "signs": [],
    "spread": "",
}


def get_disease_info(disease):
    """Return the information box content for a disease name."""
    return DISEASE_INFO.get(disease, _FALLBACK_INFO)


def get_recommendations(disease):
    """Return the list of advice lines for a disease name."""
    return RECOMMENDATIONS.get(disease, [])


def get_risk_level(disease, confidence):
    """
    Convert a prediction into a risk level.

    Confidence above 90  -> High
    Confidence 70 to 90  -> Medium
    Confidence below 70  -> Low

    When RISK_HEALTHY_IS_LOW is on, a Healthy prediction is always Low.
    """
    config = current_app.config
    if disease == "Healthy" and config.get("RISK_HEALTHY_IS_LOW", True):
        return "Low"
    if confidence > config["RISK_HIGH_THRESHOLD"]:
        return "High"
    if confidence >= config["RISK_MEDIUM_THRESHOLD"]:
        return "Medium"
    return "Low"