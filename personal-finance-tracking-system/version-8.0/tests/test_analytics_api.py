def create_expense(client, headers, name, amount, expense_date, category="Food", payment_type="Cash"):
    return client.post(
        "/expenses",
        json={
            "name": name,
            "amount": amount,
            "date": expense_date,
            "category": category,
            "payment_type": payment_type,
        },
        headers=headers
    )


# --- Feature 1: the month with the highest expenses ------------------------


def test_top_month(client, auth_headers):
    create_expense(client, auth_headers, "Food", 300, "2026-01-10")
    create_expense(client, auth_headers, "Fuel", 400, "2026-02-01")
    create_expense(client, auth_headers, "Rent", 400, "2026-02-20")

    response = client.get("/analytics/top-month", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"month": "2026-02", "total": 800.0}


def test_top_month_without_expenses(client, auth_headers):
    response = client.get("/analytics/top-month", headers=auth_headers)

    assert response.status_code == 404


# --- Feature 2: the frequency of a particular expense ----------------------


def test_frequency_counts_matching_names(client, auth_headers):
    create_expense(client, auth_headers, "Food", 100, "2026-01-01")
    create_expense(client, auth_headers, "food", 200, "2026-01-02")
    create_expense(client, auth_headers, "FOOD", 300, "2026-01-03")
    create_expense(client, auth_headers, "Rent", 400, "2026-01-04")

    response = client.get(
        "/analytics/frequency",
        params={"name": "Food"},
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json() == {"name": "Food", "count": 3}


def test_frequency_without_matches(client, auth_headers):
    create_expense(client, auth_headers, "Seafood", 100, "2026-01-01")

    response = client.get(
        "/analytics/frequency",
        params={"name": "food"},
        headers=auth_headers
    )

    assert response.json() == {"name": "food", "count": 0}


def test_frequency_requires_a_name(client, auth_headers):
    assert client.get("/analytics/frequency", headers=auth_headers).status_code == 422


# --- Feature 3: the highest spending expense ------------------------------


def test_highest_expense(client, auth_headers):
    create_expense(client, auth_headers, "Food", 300, "2026-01-10")
    create_expense(client, auth_headers, "Rent", 900, "2026-02-01")

    response = client.get("/analytics/highest", headers=auth_headers)

    assert response.status_code == 200

    expense = response.json()

    assert expense["name"] == "Rent"
    assert expense["amount"] == 900
    assert expense["date"] == "2026-02-01"


def test_highest_expense_without_expenses(client, auth_headers):
    response = client.get("/analytics/highest", headers=auth_headers)

    assert response.status_code == 404


# --- Scoping ---------------------------------------------------------------


def test_analytics_require_a_token(client):
    assert client.get("/analytics/top-month").status_code == 401
    assert client.get("/analytics/highest").status_code == 401
    assert client.get("/analytics/lowest").status_code == 401
    assert client.get("/analytics/months").status_code == 401
    assert client.get("/analytics/top-day").status_code == 401
    assert client.get("/analytics/daily", params={"month": "2026-07"}).status_code == 401
    assert client.get("/reports/month", params={"month": "2026-07"}).status_code == 401
    assert client.delete("/expenses").status_code == 401
    assert client.get("/analytics/frequency", params={"name": "Food"}).status_code == 401


def test_analytics_only_cover_the_current_user(client, auth_headers, auth_headers_for):
    create_expense(client, auth_headers, "Rent", 900, "2026-02-01")

    other_headers = auth_headers_for("other_user")
    create_expense(client, other_headers, "Food", 50, "2026-03-01")

    top_month = client.get("/analytics/top-month", headers=other_headers).json()
    highest = client.get("/analytics/highest", headers=other_headers).json()
    frequency = client.get(
        "/analytics/frequency",
        params={"name": "Rent"},
        headers=other_headers
    ).json()

    assert top_month == {"month": "2026-03", "total": 50.0}
    assert highest["name"] == "Food"
    assert frequency == {"name": "Rent", "count": 0}


# --- The lowest spending expense -------------------------------------------


def test_lowest_expense(client, auth_headers):
    create_expense(client, auth_headers, "Rent", 900, "2026-02-01")
    create_expense(client, auth_headers, "Snack", 100, "2026-01-10")

    response = client.get("/analytics/lowest", headers=auth_headers)

    assert response.status_code == 200

    expense = response.json()

    assert expense["name"] == "Snack"
    assert expense["amount"] == 100

    # Every associated attribute comes back, not just the amount.
    assert expense["date"] == "2026-01-10"
    assert expense["category"] == "Food"
    assert expense["payment_type"] == "Cash"
    assert expense["merchant"] is None
    assert expense["note"] is None


def test_lowest_expense_without_expenses(client, auth_headers):
    assert client.get("/analytics/lowest", headers=auth_headers).status_code == 404


def test_lowest_expense_only_covers_the_current_user(client, auth_headers, auth_headers_for):
    create_expense(client, auth_headers, "Rent", 900, "2026-02-01")

    other_headers = auth_headers_for("other_user")
    create_expense(client, other_headers, "Snack", 100, "2026-01-10")

    response = client.get("/analytics/lowest", headers=other_headers)

    assert response.json()["name"] == "Snack"


# --- Comparing months ------------------------------------------------------


def test_months_are_ranked_by_total(client, auth_headers):
    create_expense(client, auth_headers, "Food", 300, "2026-01-10")
    create_expense(client, auth_headers, "Fuel", 400, "2026-02-01")
    create_expense(client, auth_headers, "Rent", 400, "2026-02-20")
    create_expense(client, auth_headers, "Bus", 900, "2026-03-05")

    response = client.get("/analytics/months", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == [
        {"month": "2026-03", "total": 900.0},
        {"month": "2026-02", "total": 800.0},
        {"month": "2026-01", "total": 300.0},
    ]


def test_months_start_with_the_top_month(client, auth_headers):
    create_expense(client, auth_headers, "Food", 300, "2026-01-10")
    create_expense(client, auth_headers, "Bus", 900, "2026-03-05")

    ranking = client.get("/analytics/months", headers=auth_headers).json()
    top_month = client.get("/analytics/top-month", headers=auth_headers).json()

    assert ranking[0] == top_month


def test_months_without_expenses_is_an_empty_ranking(client, auth_headers):
    response = client.get("/analytics/months", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


# --- The busiest day of the week -------------------------------------------


def test_top_day(client, auth_headers):
    # Two Saturdays beat the single Sunday.
    create_expense(client, auth_headers, "Food", 400, "2026-07-04")
    create_expense(client, auth_headers, "Fuel", 300, "2026-07-11")
    create_expense(client, auth_headers, "Rent", 500, "2026-07-05")

    response = client.get("/analytics/top-day", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"day": "Saturday", "total": 700.0}


def test_top_day_without_expenses(client, auth_headers):
    assert client.get("/analytics/top-day", headers=auth_headers).status_code == 404


# --- Daily totals and the chart --------------------------------------------


def test_daily_totals_sum_each_day(client, auth_headers):
    create_expense(client, auth_headers, "Food", 300, "2026-07-04")
    create_expense(client, auth_headers, "Fuel", 200, "2026-07-04")
    create_expense(client, auth_headers, "Rent", 900, "2026-07-18")

    response = client.get(
        "/analytics/daily", params={"month": "2026-07"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json() == [
        {"date": "2026-07-04", "total": 500.0},
        {"date": "2026-07-18", "total": 900.0},
    ]


def test_daily_totals_reject_a_month_that_is_not_a_month(client, auth_headers):
    response = client.get(
        "/analytics/daily", params={"month": "July"}, headers=auth_headers
    )

    assert response.status_code == 400


def test_daily_totals_require_a_month(client, auth_headers):
    assert client.get("/analytics/daily", headers=auth_headers).status_code == 422


def test_the_monthly_report_is_a_self_contained_html_page(client, auth_headers):
    create_expense(client, auth_headers, "Food", 300, "2026-07-04")

    response = client.get(
        "/reports/month", params={"month": "2026-07"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    page = response.text

    assert "<svg" in page
    assert "July 2026 spending" in page

    # It has to work with no network and no JavaScript.
    assert "<script" not in page
    assert "http://" not in page
    assert "https://" not in page


def test_the_monthly_report_rejects_a_month_that_is_not_a_month(client, auth_headers):
    response = client.get(
        "/reports/month", params={"month": "2026"}, headers=auth_headers
    )

    assert response.status_code == 400


def test_the_monthly_report_only_covers_the_current_user(client, auth_headers, auth_headers_for):
    other_headers = auth_headers_for("other_user")
    create_expense(client, other_headers, "Rent", 900, "2026-07-04")

    response = client.get(
        "/reports/month", params={"month": "2026-07"}, headers=auth_headers
    )

    assert "No expenses recorded in July 2026." in response.text


# --- Deleting every expense ------------------------------------------------


def test_delete_all_expenses(client, auth_headers):
    create_expense(client, auth_headers, "Food", 100, "2026-01-01")
    create_expense(client, auth_headers, "Rent", 900, "2026-01-02")

    response = client.delete("/expenses", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["deleted"] == 2
    assert client.get("/expenses", headers=auth_headers).json() == []


def test_delete_all_expenses_leaves_another_user_alone(client, auth_headers, auth_headers_for):
    create_expense(client, auth_headers, "Rent", 900, "2026-01-02")

    other_headers = auth_headers_for("other_user")
    create_expense(client, other_headers, "Food", 50, "2026-01-03")

    client.delete("/expenses", headers=auth_headers)

    survivors = client.get("/expenses", headers=other_headers).json()

    assert len(survivors) == 1
    assert survivors[0]["name"] == "Food"


def test_delete_all_expenses_without_expenses(client, auth_headers):
    response = client.delete("/expenses", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["deleted"] == 0


def test_deleting_every_expense_is_reported_when_nothing_is_left(client, auth_headers):
    create_expense(client, auth_headers, "Food", 100, "2026-01-01")

    client.delete("/expenses", headers=auth_headers)

    assert client.get("/analytics/highest", headers=auth_headers).status_code == 404
    assert client.get("/analytics/months", headers=auth_headers).json() == []
