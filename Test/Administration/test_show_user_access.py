import requests


def test_admin_route_redirects_when_not_logged_in(base_url):
    response = requests.get(f"{base_url}/admin/user/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=0"


def test_admin_route_redirects_when_logged_in_without_permission(base_url, make_user, login_as):
    user = make_user()  # Permission créée avec tous les booléens à False par défaut

    session = login_as(user["username"], user["password"])
    response = session.get(f"{base_url}/admin/user/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_admin_route_accessible_with_admin_permission(base_url, make_user, login_as):
    user = make_user(admin=True)

    session = login_as(user["username"], user["password"])
    response = session.get(f"{base_url}/admin/user/")

    assert response.status_code == 200
    assert user["username"] in response.text


def test_admin_route_accessible_with_show_specific_account_permission(base_url, make_user, login_as):
    user = make_user(show_specific_account=True)

    session = login_as(user["username"], user["password"])
    response = session.get(f"{base_url}/admin/user/")

    assert response.status_code == 200
