from urllib.parse import urlparse, parse_qs

import requests

PLAIN_SECRET = "_pytest_client_secret"


def _get_authorization_code(session, base_url, module, scope="openid"):
    response = session.get(
        f"{base_url}/oauth/authorize",
        params={
            "client_id": module.token,
            "response_type": "code",
            "redirect_uri": f"{module.fqdn}/callback",
            "scope": scope,
        },
        allow_redirects=False,
    )
    assert response.status_code == 302, response.text
    query = parse_qs(urlparse(response.headers["Location"]).query)
    return query["code"][0]


def _exchange_code(base_url, module, code, client_secret=PLAIN_SECRET, redirect_uri=None):
    return requests.post(f"{base_url}/oauth/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri or f"{module.fqdn}/callback",
        "client_id": module.token,
        "client_secret": client_secret,
    })


def test_authorization_code_grant_issues_tokens(base_url, make_user, make_module, login_as):
    module = make_module(client_secret=PLAIN_SECRET)
    user = make_user()
    session = login_as(user["username"], user["password"])

    code = _get_authorization_code(session, base_url, module, scope="openid profile email")
    response = _exchange_code(base_url, module, code)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"].lower() == "bearer"
    assert "access_token" in body
    assert "refresh_token" in body
    assert "id_token" in body  # emis via l'extension OpenIDCode (scope openid)


def test_authorization_code_is_single_use(base_url, make_user, make_module, login_as):
    module = make_module(client_secret=PLAIN_SECRET)
    user = make_user()
    session = login_as(user["username"], user["password"])

    code = _get_authorization_code(session, base_url, module)
    first = _exchange_code(base_url, module, code)
    assert first.status_code == 200

    second = _exchange_code(base_url, module, code)
    assert second.status_code == 400


def test_token_endpoint_rejects_wrong_client_secret(base_url, make_user, make_module, login_as):
    module = make_module(client_secret=PLAIN_SECRET)
    user = make_user()
    session = login_as(user["username"], user["password"])

    code = _get_authorization_code(session, base_url, module)
    response = _exchange_code(base_url, module, code, client_secret="wrong-secret")

    assert response.status_code == 400  # invalid_client, cf. RFC 6749
    assert response.json()["error"] == "invalid_client"


def test_refresh_token_grant_issues_a_new_access_token(base_url, make_user, make_module, login_as):
    module = make_module(client_secret=PLAIN_SECRET)
    user = make_user()
    session = login_as(user["username"], user["password"])

    code = _get_authorization_code(session, base_url, module)
    first_token = _exchange_code(base_url, module, code).json()

    response = requests.post(f"{base_url}/oauth/token", data={
        "grant_type": "refresh_token",
        "refresh_token": first_token["refresh_token"],
        "client_id": module.token,
        "client_secret": PLAIN_SECRET,
    })

    assert response.status_code == 200
    assert response.json()["access_token"] != first_token["access_token"]


def test_userinfo_returns_claims_matching_requested_scope(base_url, make_user, make_module, login_as):
    module = make_module(client_secret=PLAIN_SECRET)
    user = make_user()
    session = login_as(user["username"], user["password"])

    code = _get_authorization_code(session, base_url, module, scope="openid profile email")
    token = _exchange_code(base_url, module, code).json()

    response = requests.get(
        f"{base_url}/oauth/userinfo",
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )

    assert response.status_code == 200
    claims = response.json()
    assert claims["sub"] == user["token"]
    assert claims["preferred_username"] == user["username"]
    assert "email" in claims


def test_userinfo_omits_claims_outside_requested_scope(base_url, make_user, make_module, login_as):
    """Regression : demander seulement `openid` ne doit pas divulguer email/username."""
    module = make_module(client_secret=PLAIN_SECRET)
    user = make_user()
    session = login_as(user["username"], user["password"])

    code = _get_authorization_code(session, base_url, module, scope="openid")
    token = _exchange_code(base_url, module, code).json()

    response = requests.get(
        f"{base_url}/oauth/userinfo",
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )

    claims = response.json()
    assert claims["sub"] == user["token"]
    assert "email" not in claims
    assert "preferred_username" not in claims


def test_userinfo_rejects_missing_token(base_url):
    response = requests.get(f"{base_url}/oauth/userinfo")

    assert response.status_code == 401


def test_userinfo_rejects_invalid_token(base_url):
    response = requests.get(
        f"{base_url}/oauth/userinfo", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_discovery_document_exposes_expected_endpoints(base_url):
    response = requests.get(f"{base_url}/.well-known/openid-configuration")

    assert response.status_code == 200
    body = response.json()
    assert body["authorization_endpoint"].endswith("/oauth/authorize")
    assert body["token_endpoint"].endswith("/oauth/token")
    assert body["userinfo_endpoint"].endswith("/oauth/userinfo")
    assert body["jwks_uri"].endswith("/oauth/jwks.json")
    assert "openid" in body["scopes_supported"]
    assert "authorization_code" in body["grant_types_supported"]
    assert "refresh_token" in body["grant_types_supported"]


def test_jwks_endpoint_exposes_a_public_rsa_key(base_url):
    response = requests.get(f"{base_url}/oauth/jwks.json")

    assert response.status_code == 200
    keys = response.json()["keys"]
    assert len(keys) >= 1
    assert keys[0]["kty"] == "RSA"
    # Cle publique uniquement : jamais d'exposant/module prive dans un JWKS.
    assert "d" not in keys[0]
