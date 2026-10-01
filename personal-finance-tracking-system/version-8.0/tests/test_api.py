from datetime import date


def create_expense(client, headers, name="Food", amount=2500.0, **extra):
    payload = {
        "name": name,
        "amount": amount,
        "category": "Food",
        "payment_type": "Cash",
    }
    payload.update(extra)

    return client.post("/expenses", json=payload, headers=headers)


def test_get_expenses(client, auth_headers):
      assert create_expense(client, auth_headers).status_code == 201

      response = client.get("/expenses", headers=auth_headers)
      assert response.status_code == 200

      expenses = response.json()

      assert isinstance(expenses, list)

      for expense in expenses:
            assert isinstance(expense, dict)

            assert "id" in expense

            assert "name" in expense
            assert "amount" in expense
            assert "date" in expense
            assert "category" in expense
            assert "payment_type" in expense

            assert isinstance(expense["id"], int)

            assert isinstance(expense["name"], str)

            assert isinstance(expense["amount"], float)

            assert isinstance(expense["date"], str)


def test_create_expense(client, auth_headers):
      response = create_expense(client, auth_headers, name="Test Food", amount=2500)

      assert response.status_code == 201
      assert response.json()["result"] == "SUCCESS"

      expense =  response.json()["expense"]
      assert expense["name"] == "Test Food"
      assert expense["amount"] == 2500


def test_create_expense_with_an_explicit_date(client, auth_headers):
      response = create_expense(
            client, auth_headers, date="2026-07-14"
      )

      assert response.status_code == 201
      assert response.json()["expense"]["date"] == "2026-07-14"


def test_create_expense_defaults_to_today(client, auth_headers):
      response = create_expense(client, auth_headers)

      assert response.status_code == 201
      assert response.json()["expense"]["date"] == date.today().isoformat()


def test_create_expense_with_a_malformed_date(client, auth_headers):
      response = create_expense(client, auth_headers, date="14-07-2026")

      assert response.status_code == 422


def test_create_expense_returns_category_and_payment_type(client, auth_headers):
      response = create_expense(
            client, auth_headers, category="Rent", payment_type="Transfer"
      )

      expense = response.json()["expense"]

      assert expense["category"] == "Rent"
      assert expense["payment_type"] == "Transfer"


def test_create_expense_stores_the_canonical_category(client, auth_headers):
      response = create_expense(client, auth_headers, category="  food  ")

      assert response.status_code == 201
      assert response.json()["expense"]["category"] == "Food"


def test_create_expense_stores_the_canonical_payment_type(client, auth_headers):
      response = create_expense(client, auth_headers, payment_type="mobile money")

      assert response.status_code == 201
      assert response.json()["expense"]["payment_type"] == "Mobile Money"


def test_create_expense_requires_a_category(client, auth_headers):
      response = client.post(
            "/expenses",
            json={"name": "Food", "amount": 100, "payment_type": "Cash"},
            headers=auth_headers
      )

      assert response.status_code == 422


def test_create_expense_requires_a_payment_type(client, auth_headers):
      response = client.post(
            "/expenses",
            json={"name": "Food", "amount": 100, "category": "Food"},
            headers=auth_headers
      )

      assert response.status_code == 422


def test_create_expense_rejects_an_unknown_category(client, auth_headers):
      response = create_expense(client, auth_headers, category="Groceries")

      assert response.status_code == 400
      assert "Category must be one of" in response.json()["detail"]


def test_create_expense_rejects_an_unknown_payment_type(client, auth_headers):
      response = create_expense(client, auth_headers, payment_type="Barter")

      assert response.status_code == 400
      assert "Payment type must be one of" in response.json()["detail"]


def test_update_expense_changes_category_and_payment_type(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000, "category": "transport", "payment_type": "card"},
            headers=auth_headers
      )

      assert response.status_code == 200

      updated = client.get(f"/expenses/{expense_id}", headers=auth_headers).json()
      assert updated["category"] == "Transport"
      assert updated["payment_type"] == "Card"


def test_update_expense_keeps_the_category_when_it_is_omitted(client, auth_headers):
      expense_id = create_expense(
            client, auth_headers, category="Rent"
      ).json()["expense"]["id"]

      client.put(f"/expenses/{expense_id}", json={"amount": 3000}, headers=auth_headers)

      updated = client.get(f"/expenses/{expense_id}", headers=auth_headers).json()
      assert updated["category"] == "Rent"


def test_update_expense_rejects_an_unknown_category(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000, "category": "Groceries"},
            headers=auth_headers
      )

      assert response.status_code == 400
      assert "Category must be one of" in response.json()["detail"]


# --- Merchant and note ------------------------------------------------------


def test_create_expense_stores_merchant_and_note(client, auth_headers):
      response = create_expense(
            client, auth_headers, merchant="  Shoprite  ", note="weekly shop"
      )

      expense = response.json()["expense"]

      # Trimmed on the way in, like every other piece of free text.
      assert expense["merchant"] == "Shoprite"
      assert expense["note"] == "weekly shop"


def test_create_expense_without_merchant_or_note(client, auth_headers):
      expense = create_expense(client, auth_headers).json()["expense"]

      assert expense["merchant"] is None
      assert expense["note"] is None


def test_update_expense_changes_merchant_and_note(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000, "merchant": "Shoprite", "note": "weekly shop"},
            headers=auth_headers
      )

      updated = client.get(f"/expenses/{expense_id}", headers=auth_headers).json()

      assert updated["merchant"] == "Shoprite"
      assert updated["note"] == "weekly shop"


def test_update_expense_keeps_merchant_and_note_when_omitted(client, auth_headers):
      expense_id = create_expense(
            client, auth_headers, merchant="Shoprite", note="weekly shop"
      ).json()["expense"]["id"]

      client.put(f"/expenses/{expense_id}", json={"amount": 3000}, headers=auth_headers)

      updated = client.get(f"/expenses/{expense_id}", headers=auth_headers).json()

      assert updated["merchant"] == "Shoprite"
      assert updated["note"] == "weekly shop"


def test_update_expense_clears_merchant_and_note_with_an_empty_string(client, auth_headers):
      expense_id = create_expense(
            client, auth_headers, merchant="Shoprite", note="weekly shop"
      ).json()["expense"]["id"]

      client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000, "merchant": "", "note": ""},
            headers=auth_headers
      )

      updated = client.get(f"/expenses/{expense_id}", headers=auth_headers).json()

      assert updated["merchant"] is None
      assert updated["note"] is None


def test_update_expense_rejects_an_unknown_payment_type(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000, "payment_type": "Barter"},
            headers=auth_headers
      )

      assert response.status_code == 400
      assert "Payment type must be one of" in response.json()["detail"]


def test_update_expense_changes_the_name_and_date(client, auth_headers):
      """A typo in what you bought, or a mis-keyed date, is correctable."""
      expense_id = create_expense(
            client, auth_headers, name="Grocerys", date="2026-09-02"
      ).json()["expense"]["id"]

      response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 24500, "name": "Groceries", "date": "2026-08-30"},
            headers=auth_headers
      )

      assert response.status_code == 200

      updated = client.get(f"/expenses/{expense_id}", headers=auth_headers).json()

      assert updated["name"] == "Groceries"
      assert updated["date"] == "2026-08-30"


def test_update_expense_keeps_the_name_and_date_when_omitted(client, auth_headers):
      expense_id = create_expense(
            client, auth_headers, name="Groceries", date="2026-09-02"
      ).json()["expense"]["id"]

      client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000},
            headers=auth_headers
      )

      updated = client.get(f"/expenses/{expense_id}", headers=auth_headers).json()

      assert updated["name"] == "Groceries"
      assert updated["date"] == "2026-09-02"


def test_update_expense_rejects_an_empty_name(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000, "name": "   "},
            headers=auth_headers
      )

      assert response.status_code == 400
      assert response.json()["detail"] == "Name cannot be empty"


def test_update_expense_rejects_a_malformed_date(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000, "date": "the twelfth"},
            headers=auth_headers
      )

      # Parsed at the wire, so this never reaches the service.
      assert response.status_code == 422


def test_create_expense_with_an_empty_name(client, auth_headers):
      response = create_expense(client, auth_headers, name="   ")

      assert response.status_code == 400
      assert response.json()["detail"] == "Name cannot be empty"


def test_create_expense_with_a_non_positive_amount(client, auth_headers):
      response = create_expense(client, auth_headers, amount=0)

      assert response.status_code == 400
      assert response.json()["detail"] == "Amount must be greater than zero"


def test_get_expense_not_found(client, auth_headers):
      response = client.get("/expenses/999", headers=auth_headers)

      assert response.status_code == 404


def test_update_expense(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 3000},
            headers=auth_headers
      )

      assert response.status_code == 200
      assert response.json()["message"] == "Expense updated successfully"

      updated = client.get(f"/expenses/{expense_id}", headers=auth_headers).json()
      assert updated["amount"] == 3000


def test_update_expense_with_a_non_positive_amount(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      response = client.put(
            f"/expenses/{expense_id}",
            json={"amount": 0},
            headers=auth_headers
      )

      assert response.status_code == 400


def test_delete_expense(client, auth_headers):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      response = client.delete(f"/expenses/{expense_id}", headers=auth_headers)

      assert response.status_code == 200
      assert client.get(f"/expenses/{expense_id}", headers=auth_headers).status_code == 404


# --- Authentication --------------------------------------------------------


def test_expenses_require_a_token(client):
      assert client.get("/expenses").status_code == 401


def test_expenses_reject_a_bad_token(client):
      response = client.get(
            "/expenses",
            headers={"Authorization": "Bearer not-a-real-token"}
      )

      assert response.status_code == 401


def test_expense_writes_require_a_token(client):
      assert client.post("/expenses", json={"name": "Food", "amount": 100}).status_code == 401
      assert client.delete("/expenses/1").status_code == 401


def test_registering_the_same_username_twice_conflicts(client):
      first = client.post(
            "/register",
            json={"username": "api_user", "password": "TestPassword123"}
      )
      assert first.status_code == 201

      response = client.post(
            "/register",
            json={"username": "api_user", "password": "TestPassword123"}
      )

      assert response.status_code == 409


def test_login_with_a_wrong_password(client):
      client.post(
            "/register",
            json={"username": "api_user", "password": "TestPassword123"}
      )

      response = client.post(
            "/login",
            json={"username": "api_user", "password": "wrong-password"}
      )

      assert response.status_code == 401


# --- Per-user isolation ----------------------------------------------------


def test_another_users_expense_is_invisible(client, auth_headers, auth_headers_for):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      other_headers = auth_headers_for("other_user")

      assert client.get(f"/expenses/{expense_id}", headers=other_headers).status_code == 404
      assert client.get("/expenses", headers=other_headers).json() == []


def test_another_user_cannot_delete_your_expense(client, auth_headers, auth_headers_for):
      expense_id = create_expense(client, auth_headers).json()["expense"]["id"]

      other_headers = auth_headers_for("other_user")

      assert client.delete(f"/expenses/{expense_id}", headers=other_headers).status_code == 404
      assert client.get(f"/expenses/{expense_id}", headers=auth_headers).status_code == 200


# --- Feature 4: search -----------------------------------------------------


def test_search_expenses_by_name(client, auth_headers):
      create_expense(client, auth_headers, name="Food", amount=100)
      create_expense(client, auth_headers, name="Seafood", amount=200)
      create_expense(client, auth_headers, name="Rent", amount=300)

      response = client.get("/expenses/search", params={"name": "foo"}, headers=auth_headers)

      assert response.status_code == 200

      matches = response.json()

      assert [expense["name"] for expense in matches] == ["Food", "Seafood"]

      # Every attribute is present, not just the name.
      assert set(matches[0]) == {
            "id", "name", "amount", "date", "category", "payment_type",
            "merchant", "note",
      }


def test_search_expenses_without_matches(client, auth_headers):
      create_expense(client, auth_headers, name="Rent")

      response = client.get("/expenses/search", params={"name": "food"}, headers=auth_headers)

      assert response.json() == []


def test_search_expenses_treats_wildcards_literally(client, auth_headers):
      create_expense(client, auth_headers, name="Food")
      create_expense(client, auth_headers, name="50% off")

      response = client.get("/expenses/search", params={"name": "%"}, headers=auth_headers)

      assert [expense["name"] for expense in response.json()] == ["50% off"]


def test_search_expenses_requires_a_name(client, auth_headers):
      assert client.get("/expenses/search", headers=auth_headers).status_code == 422


def test_search_expenses_is_scoped_to_the_user(client, auth_headers, auth_headers_for):
      create_expense(client, auth_headers, name="Food")

      other_headers = auth_headers_for("other_user")

      response = client.get("/expenses/search", params={"name": "foo"}, headers=other_headers)

      assert response.json() == []


def test_the_chart_fragment_is_the_same_chart_without_the_document(client, auth_headers):
      """The browser client injects this into a page it already has."""
      create_expense(client, auth_headers, amount=2500, date="2026-09-02")

      fragment = client.get(
            "/reports/month.fragment",
            params={"month": "2026-09"},
            headers=auth_headers
      )
      document = client.get(
            "/reports/month",
            params={"month": "2026-09"},
            headers=auth_headers
      )

      assert fragment.status_code == 200

      body = fragment.json()

      assert "spending-chart" in body["css"]
      assert "<html" not in body["html"]
      assert "<style" not in body["html"]

      # The same markup the standalone document carries, so there is one
      # renderer rather than two that drift.
      assert body["html"] in document.text
      assert body["css"] in document.text


def test_the_chart_fragment_rejects_a_month_that_is_not_a_month(client, auth_headers):
      response = client.get(
            "/reports/month.fragment",
            params={"month": "September"},
            headers=auth_headers
      )

      assert response.status_code == 400
      assert response.json()["detail"] == "Month must be in YYYY-MM format"


def test_the_chart_fragment_needs_a_session(client):
      response = client.get("/reports/month.fragment", params={"month": "2026-09"})

      assert response.status_code == 401
