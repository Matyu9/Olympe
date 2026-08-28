import requests


def _login_set_cookie_headers(base_url, user):
    response = requests.post(
        f"{base_url}/sso/login/",
        data={"username": user["username"], "password": user["password"]},
        allow_redirects=False,
    )
    return response, response.raw.headers.getlist("Set-Cookie")


def test_login_cookies_are_httponly_and_samesite(base_url, make_user):
    """Régression sécurité : sans `httponly`, un XSS peut lire les cookies `token`/`validation` ;
    sans `samesite`, ils partent aussi sur des requêtes cross-site en arrière-plan (CSRF)."""
    user = make_user()

    _, set_cookie_headers = _login_set_cookie_headers(base_url, user)

    assert len(set_cookie_headers) >= 2
    for header in set_cookie_headers:
        assert "HttpOnly" in header
        assert "SameSite=Lax" in header


def test_login_cookie_secure_flag_matches_debug_mode(base_url, make_user, config):
    """`secure` doit être désactivé uniquement quand `debug_mode` l'est (dev local en http://),
    sinon les cookies de session ne seraient jamais envoyés en HTTPS en production."""
    user = make_user()
    debug_mode = config["modules"][0]["debug_mode"]

    _, set_cookie_headers = _login_set_cookie_headers(base_url, user)

    for header in set_cookie_headers:
        if debug_mode:
            assert "; Secure" not in header
        else:
            assert "; Secure" in header


def _domain_attribute(set_cookie_header):
    for part in set_cookie_header.split(";"):
        part = part.strip()
        if part.lower().startswith("domain="):
            return part.split("=", 1)[1]
    return None


def test_logout_clears_cookies_with_matching_domain(base_url, make_user):
    """Régression : le logout doit reposer le même `domain=` que celui utilisé au login (une fois
    normalisé par Werkzeug), sinon le navigateur ne remplace jamais le cookie existant et la
    session reste valide après une "déconnexion"."""
    user = make_user()

    login_response = requests.post(
        f"{base_url}/sso/login/",
        data={"username": user["username"], "password": user["password"]},
        allow_redirects=False,
    )
    login_domains = {
        _domain_attribute(header) for header in login_response.raw.headers.getlist("Set-Cookie")
    }
    assert login_domains and None not in login_domains

    session = requests.Session()
    session.cookies.update(login_response.cookies)
    logout_response = session.get(f"{base_url}/sso/logout/", allow_redirects=False)
    logout_set_cookie_headers = logout_response.raw.headers.getlist("Set-Cookie")

    assert len(logout_set_cookie_headers) >= 2
    for header in logout_set_cookie_headers:
        assert _domain_attribute(header) in login_domains
