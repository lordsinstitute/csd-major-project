"""History page: columns, ordering, pagination, search, filters and privacy."""

from datetime import date, timedelta

from tests.helpers import add_record, seed_three
from utils.history_query import parse_filters


def get_text(client, **params):
    response = client.get("/history", query_string=params)
    assert response.status_code == 200
    return response.get_data(as_text=True)


# ------------------------------------------------------------ basic page
def test_empty_history_shows_message(auth_client):
    assert "No scans yet" in get_text(auth_client)


def test_history_shows_required_columns_and_values(app, auth_client, farmer):
    add_record(app, farmer["id"], batch_name="Alpha", sick_birds=12, dead_birds=2)
    text = get_text(auth_client)
    for heading in ("Date", "Farmer", "Batch", "Disease", "Confidence", "Sick Birds", "Dead Birds"):
        assert heading in text
    assert "Alpha" in text
    assert "Ramesh" in text
    assert date.today().strftime("%d-%m-%Y") in text
    assert "91.0%" in text


def test_newest_scan_comes_first(app, auth_client, farmer):
    add_record(app, farmer["id"], batch_name="OldBatch", date=date.today() - timedelta(days=10))
    add_record(app, farmer["id"], batch_name="NewBatch", date=date.today())
    text = get_text(auth_client)
    assert text.index("NewBatch") < text.index("OldBatch")


# ------------------------------------------------------------ pagination
def test_pagination(app, auth_client, farmer):
    for number in range(25):
        add_record(app, farmer["id"], batch_name=f"Batch{number:02d}")

    first = get_text(auth_client)
    assert "Showing 1-10 of 25 scans" in first
    assert "Batch24" in first
    assert "Batch14" not in first

    last = get_text(auth_client, page=3)
    assert "Showing 21-25 of 25 scans" in last
    assert "Batch00" in last
    assert "Batch24" not in last


def test_page_beyond_last_falls_back_to_last_page(app, auth_client, farmer):
    for number in range(25):
        add_record(app, farmer["id"], batch_name=f"Batch{number:02d}")
    assert "Showing 21-25 of 25 scans" in get_text(auth_client, page=999)


def test_bad_page_number_shows_first_page(app, auth_client, farmer):
    for number in range(12):
        add_record(app, farmer["id"], batch_name=f"Batch{number:02d}")
    assert "Showing 1-10 of 12 scans" in get_text(auth_client, page="abc")
    assert "Showing 1-10 of 12 scans" in get_text(auth_client, page=-4)


def test_page_links_keep_filters(app, auth_client, farmer):
    for number in range(15):
        add_record(app, farmer["id"], batch_name=f"Batch{number:02d}")
    text = get_text(auth_client, disease="Salmonella")
    assert "page=2" in text
    assert "disease=Salmonella" in text


# ----------------------------------------------------------------- search
def test_search_by_batch_name_ignores_case(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    text = get_text(auth_client, q="ALPH")
    assert "Alpha" in text
    assert "Bravo" not in text


def test_search_by_disease_name(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    text = get_text(auth_client, q="newcastle")
    assert "Charlie" in text
    assert "Alpha" not in text
    assert "Bravo" not in text


def test_search_by_farmer_and_farm_name(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    for term in ("Ramesh", "Green Valley"):
        text = get_text(auth_client, q=term)
        assert "Alpha" in text and "Bravo" in text and "Charlie" in text


def test_search_treats_wildcards_as_plain_text(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    for term in ("%", "_"):
        assert "No scans match" in get_text(auth_client, q=term)


# ---------------------------------------------------------------- filters
def test_filter_by_disease(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    text = get_text(auth_client, disease="Salmonella")
    assert "Bravo" in text
    assert "Alpha" not in text
    assert "Charlie" not in text


def test_filter_by_risk_level(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    text = get_text(auth_client, risk="Medium")
    assert "Charlie" in text
    assert "Alpha" not in text
    assert "Bravo" not in text


def test_filter_by_date_range(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    today = date.today()

    after = get_text(auth_client, date_from=(today - timedelta(days=15)).isoformat())
    assert "Bravo" in after and "Charlie" in after and "Alpha" not in after

    before = get_text(auth_client, date_to=(today - timedelta(days=15)).isoformat())
    assert "Alpha" in before and "Bravo" not in before

    between = get_text(
        auth_client,
        date_from=(today - timedelta(days=15)).isoformat(),
        date_to=(today - timedelta(days=5)).isoformat(),
    )
    assert "Bravo" in between
    assert "Alpha" not in between and "Charlie" not in between


def test_reversed_date_range_is_swapped(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    today = date.today()
    text = get_text(
        auth_client,
        date_from=(today - timedelta(days=5)).isoformat(),
        date_to=(today - timedelta(days=15)).isoformat(),
    )
    assert "Bravo" in text
    assert "Alpha" not in text


def test_invalid_filter_values_are_ignored(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    text = get_text(
        auth_client, disease="Plague", risk="Extreme", date_from="not-a-date"
    )
    assert "Alpha" in text and "Bravo" in text and "Charlie" in text


def test_search_and_filter_combine(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    text = get_text(auth_client, q="Bravo", disease="Newcastle")
    assert "No scans match" in text


def test_parse_filters_cleans_values(app):
    with app.test_request_context(
        "/history?disease=Foo&risk=Bar&date_from=bad&date_to=2025-01-31&q=%20hi%20"
    ):
        from flask import request

        filters = parse_filters(request.args)
    assert filters == {
        "q": "hi",
        "disease": "",
        "risk": "",
        "date_from": "",
        "date_to": "2025-01-31",
    }


# ---------------------------------------------------------------- privacy
def test_farmers_only_see_their_own_scans(
    app, auth_client, second_client, farmer, second_farmer
):
    add_record(app, farmer["id"], batch_name="MineOnly")
    add_record(app, second_farmer["id"], batch_name="TheirsOnly")

    own = get_text(auth_client)
    assert "MineOnly" in own and "TheirsOnly" not in own

    theirs = get_text(second_client)
    assert "TheirsOnly" in theirs and "MineOnly" not in theirs


def test_shared_scope_shows_every_farm(
    app, auth_client, farmer, second_farmer
):
    app.config["DASHBOARD_SCOPE"] = "all"
    add_record(app, farmer["id"], batch_name="MineOnly")
    add_record(app, second_farmer["id"], batch_name="TheirsOnly")

    text = get_text(auth_client)
    assert "MineOnly" in text and "TheirsOnly" in text