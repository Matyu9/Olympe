import requests


def test_wrong_password_redirects_with_error_and_sets_no_cookie(base_url, make_user):
    user = make_user()

    response = requests.post(
        f"{base_url}/sso/login/",
        data={"username": user["username"], "password": "not-the-right-password"},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=1"
    assert "token" not in response.cookies


def test_correct_password_sets_auth_cookies(base_url, make_user):
    user = make_user()

    response = requests.post(
        f"{base_url}/sso/login/",
        data={"username": user["username"], "password": user["password"]},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.cookies["token"] == user["token"]
    assert "validation" in response.cookies


def test_unknown_username_redirects_with_error(base_url):
    response = requests.post(
        f"{base_url}/sso/login/",
        data={"username": "_does_not_exist_", "password": "whatever"},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=1"


def test_desactivated_account_is_blocked_from_protected_routes(base_url, make_user, login_as):
    user = make_user(desactivated=True)

    session = login_as(user["username"], user["password"])
    response = session.get(f"{base_url}/admin/user/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=2"
