from datetime import datetime, date

from fastapi.testclient import TestClient

from main import app
import app.routes as routes


class DummyResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row

    def scalar_one(self):
        return self._row


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_row(user_id: int = 1, email: str = "jean.dupont@example.com") -> dict:
    return {
        "id": user_id,
        "nom": "Dupont",
        "prenom": "Jean",
        "email": email,
        "sexe": "homme",
        "abonnement": "freemium",
        "date_inscription": datetime.now(),
        "actif": True,
    }


def _aliment_row(aliment_id: int = 10) -> dict:
    return {
        "id": aliment_id,
        "nom": "Riz blanc",
        "calories_100g": 130.0,
        "categorie": "Féculents",
        "source_dataset": "manual",
        "created_at": datetime.now(),
    }


# ---------------------------------------------------------------------------
# POST /users
# ---------------------------------------------------------------------------

def test_create_user_success(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: None)
    monkeypatch.setattr(routes, "execute_write", lambda *a, **kw: DummyResult(_user_row()))

    resp = client.post(
        "/users",
        json={
            "nom": "Dupont", "prenom": "Jean",
            "email": "jean.dupont@example.com",
            "password": "secret123", "sexe": "homme",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "jean.dupont@example.com"
    assert data["nom"] == "Dupont"
    assert data["prenom"] == "Jean"


def test_create_user_duplicate_email(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: {"id": 1})

    resp = client.post(
        "/users",
        json={"nom": "Dupont", "prenom": "Jean", "email": "jean.dupont@example.com", "password": "secret123"},
    )
    assert resp.status_code == 400


def test_create_user_invalid_email():
    resp = client.post(
        "/users",
        json={"nom": "Dupont", "prenom": "Jean", "email": "not-an-email", "password": "secret123"},
    )
    assert resp.status_code == 422


def test_create_user_password_too_short():
    resp = client.post(
        "/users",
        json={"nom": "Dupont", "prenom": "Jean", "email": "jean.dupont@example.com", "password": "abc"},
    )
    assert resp.status_code == 422


def test_create_user_missing_required_fields():
    resp = client.post("/users", json={"nom": "Dupont"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/{user_id}
# ---------------------------------------------------------------------------

def test_get_user_success(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: _user_row())

    resp = client.get("/users/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


def test_get_user_not_found(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: None)

    resp = client.get("/users/999")
    assert resp.status_code == 404
    # message varies with Accept-Language (EN: "User not found.", FR: "Utilisateur introuvable")
    assert "not found" in resp.json()["detail"].lower() or "introuvable" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}
# ---------------------------------------------------------------------------

def test_delete_user_success(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: {"id": 1})
    monkeypatch.setattr(routes, "execute_write", lambda *a, **kw: None)

    resp = client.delete("/users/1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert resp.json()["user_id"] == 1


def test_delete_user_not_found(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: None)

    resp = client.delete("/users/999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /aliments
# ---------------------------------------------------------------------------

def test_create_aliment_success(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: None)
    monkeypatch.setattr(routes, "execute_write", lambda *a, **kw: DummyResult(_aliment_row()))

    resp = client.post("/aliments", json={"nom": "Riz blanc", "calories_100g": 130})
    assert resp.status_code == 200
    assert resp.json()["nom"] == "Riz blanc"


def test_create_aliment_duplicate(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: {"id": 10})

    resp = client.post("/aliments", json={"nom": "Riz blanc", "calories_100g": 130})
    assert resp.status_code == 400


def test_create_aliment_negative_calories():
    resp = client.post("/aliments", json={"nom": "Test", "calories_100g": -10})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /aliments
# ---------------------------------------------------------------------------

def test_list_aliments(monkeypatch):
    monkeypatch.setattr(routes, "fetch_all", lambda *a, **kw: [_aliment_row(), _aliment_row(20)])

    resp = client.get("/aliments")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_aliments_with_query(monkeypatch):
    monkeypatch.setattr(routes, "fetch_all", lambda *a, **kw: [_aliment_row()])

    resp = client.get("/aliments?query=riz")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}/subscription
# ---------------------------------------------------------------------------

def test_update_subscription_success(monkeypatch):
    updated = {**_user_row(), "abonnement": "premium"}
    call_count = {"n": 0}

    def fake_fetch_one(*a, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return {"id": 1}
        return updated

    monkeypatch.setattr(routes, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(routes, "execute_write", lambda *a, **kw: DummyResult(updated))

    resp = client.patch("/users/1/subscription", json={"abonnement": "premium"})
    assert resp.status_code == 200
    assert resp.json()["abonnement"] == "premium"


def test_update_subscription_invalid_value(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: {"id": 1})

    resp = client.patch("/users/1/subscription", json={"abonnement": "vip_gold"})
    assert resp.status_code == 400


def test_update_subscription_user_not_found(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: None)

    resp = client.patch("/users/999/subscription", json={"abonnement": "premium"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /users/{user_id}/metrics
# ---------------------------------------------------------------------------

def test_get_metrics_success(monkeypatch):
    metrics = [
        {"date_mesure": date(2026, 5, 1), "poids_kg": 75.0, "heures_sommeil": 7.5, "bpm_repos": 65},
        {"date_mesure": date(2026, 5, 2), "poids_kg": 74.8, "heures_sommeil": 8.0, "bpm_repos": 63},
    ]
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: {"id": 1})
    monkeypatch.setattr(routes, "fetch_all", lambda *a, **kw: metrics)

    resp = client.get("/users/1/metrics")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_metrics_user_not_found(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: None)

    resp = client.get("/users/999/metrics")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /objectifs
# ---------------------------------------------------------------------------

def test_list_objectifs(monkeypatch):
    objectifs = [
        {"id": 1, "libelle": "Perte de poids", "description": "Réduire la masse graisseuse"},
        {"id": 2, "libelle": "Prise de masse", "description": "Augmenter la masse musculaire"},
    ]
    monkeypatch.setattr(routes, "fetch_all", lambda *a, **kw: objectifs)

    resp = client.get("/objectifs")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    assert resp.json()[0]["libelle"] == "Perte de poids"


# ---------------------------------------------------------------------------
# DELETE /meals/{meal_id}
# ---------------------------------------------------------------------------

def test_delete_meal_success(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: {"id": 5})
    monkeypatch.setattr(routes, "execute_write", lambda *a, **kw: None)

    resp = client.delete("/meals/5")
    assert resp.status_code == 200
    assert resp.json()["meal_id"] == 5


def test_delete_meal_not_found(monkeypatch):
    monkeypatch.setattr(routes, "fetch_one", lambda *a, **kw: None)

    resp = client.delete("/meals/999")
    assert resp.status_code == 404
