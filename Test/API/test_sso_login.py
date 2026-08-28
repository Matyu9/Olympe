import pyotp
import requests

from Utils.Database.user import User


def test_correct_credentials_return_success(base_url, make_user):
    user = make_user()

    response = requests.post(f"{base_url}/api/sso/login", json={
        "username": user["username"], "password": user["password"],
    })

    assert response.status_code == 200
    body = response.json()
    assert body["status_code"] == 200
    assert body["credentials_status"] is True
    assert body["unique_id"] == user["token"]
    assert body["secret_id"]  # le secret_token partage, utilise par les modules Cantina


def test_wrong_password_returns_401(base_url, make_user):
    user = make_user()

    response = requests.post(f"{base_url}/api/sso/login", json={
        "username": user["username"], "password": "not-the-right-password",
    })

    assert response.status_code == 200  # l'API renvoie toujours du JSON 200, le vrai statut est dans le corps
    body = response.json()
    assert body["status_code"] == 401
    assert body["credentials_status"] is False


def test_unknown_username_returns_401(base_url):
    response = requests.post(f"{base_url}/api/sso/login", json={
        "username": "_does_not_exist_", "password": "whatever",
    })

    assert response.json()["status_code"] == 401


def test_a2f_enabled_without_code_returns_418(base_url, make_user, db_session):
    user = make_user()
    secret = pyotp.random_base32()
    db_session.query(User).filter(User.token == user["token"]).update({"A2F": True, "A2F_secret": secret})
    db_session.commit()

    response = requests.post(f"{base_url}/api/sso/login", json={
        "username": user["username"], "password": user["password"],
    })

    assert response.json()["status_code"] == 418
    assert response.json()["credentials_status"] is False


def test_a2f_enabled_with_valid_code_succeeds(base_url, make_user, db_session):
    user = make_user()
    secret = pyotp.random_base32()
    db_session.query(User).filter(User.token == user["token"]).update({"A2F": True, "A2F_secret": secret})
    db_session.commit()

    response = requests.post(f"{base_url}/api/sso/login", json={
        "username": user["username"], "password": user["password"],
        "dfa_code": pyotp.TOTP(secret).now(),
    })

    body = response.json()
    assert body["status_code"] == 200
    assert body["credentials_status"] is True
    assert body["unique_id"] == user["token"]


def test_a2f_enabled_with_wrong_code_returns_401(base_url, make_user, db_session):
    user = make_user()
    secret = pyotp.random_base32()
    db_session.query(User).filter(User.token == user["token"]).update({"A2F": True, "A2F_secret": secret})
    db_session.commit()

    response = requests.post(f"{base_url}/api/sso/login", json={
        "username": user["username"], "password": user["password"], "dfa_code": "000000",
    })

    assert response.json()["status_code"] == 401
