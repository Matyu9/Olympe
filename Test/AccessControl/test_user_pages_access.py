import pytest
import requests

from Utils.Database.modules import Module

# Repetitif par nature (une garde presque identique verifiee route par route) : exclu du
# `pytest` classique, voir pytest.ini. Lancer avec `pytest -m access_control`.
pytestmark = pytest.mark.access_control

# Ces 4 pages (Cogs/User/*) ne demandent qu'une connexion valide, aucune permission
# particuliere - contrairement aux pages Administration/*.
USER_PAGES = ["/", "/user_space/", "/2FA/add/", "/email/verif/"]


@pytest.fixture()
def olympe_module(db_session):
    """Les 4 pages Cogs/User/* redirigent un compte desactive vers le fqdn du module "olympe"
    en base plutot que vers sso_login directement (cf. desactivated_redirect='olympe_fqdn' dans
    Utils/verify_login.py) - il faut donc que ce module existe pour exercer ce chemin."""
    module = Module(token="_pytest_olympe_module", name="olympe", fqdn="https://olympe.example.invalid")
    db_session.add(module)
    db_session.commit()
    yield module
    db_session.query(Module).filter(Module.token == "_pytest_olympe_module").delete()
    db_session.commit()


@pytest.mark.parametrize("path", USER_PAGES)
def test_page_accessible_when_logged_in(base_url, make_user, login_as, path):
    user = make_user()
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}{path}", allow_redirects=False)

    assert response.status_code == 200


@pytest.mark.parametrize("path", USER_PAGES)
def test_page_redirects_to_olympe_fqdn_when_desactivated(base_url, make_user, login_as, olympe_module, path):
    user = make_user(desactivated=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}{path}", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == f"{olympe_module.fqdn}/sso/login/?error=2"


def test_home_page_redirects_when_not_logged_in(base_url):
    response = requests.get(f"{base_url}/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=0"
