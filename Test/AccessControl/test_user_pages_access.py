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
def ensure_olympe_module(db_session):
    """Les 4 pages Cogs/User/* redirigent un compte desactive vers le fqdn du module "olympe"
    en base plutot que vers sso_login directement (cf. desactivated_redirect='olympe_fqdn' dans
    Utils/verify_login.py) - il faut donc que ce module existe pour exercer ce chemin. Reutilise
    la ligne "olympe" existante (fqdn sauvegarde/restaure) plutot que d'en creer une deuxieme -
    la colonne `name` n'est pas unique en base, un doublon rendrait le lookup non deterministe."""
    existing = db_session.query(Module).filter(Module.name == "olympe").first()
    test_fqdn = "https://olympe.example.invalid"

    if existing is not None:
        original_fqdn = existing.fqdn
        db_session.query(Module).filter(Module.id == existing.id).update({"fqdn": test_fqdn})
        db_session.commit()
        yield test_fqdn
        db_session.query(Module).filter(Module.id == existing.id).update({"fqdn": original_fqdn})
        db_session.commit()
    else:
        token = "_pytest_olympe_module"
        db_session.add(Module(token=token, name="olympe", fqdn=test_fqdn))
        db_session.commit()
        yield test_fqdn
        db_session.query(Module).filter(Module.token == token).delete()
        db_session.commit()


@pytest.fixture()
def hide_olympe_module(db_session):
    """Masque temporairement la ligne "olympe" (renommee) pour tester la regression corrigee :
    Cogs/User/* plantait en 500 (AttributeError) si aucun module "olympe" n'existait en base,
    au lieu de retomber sur la redirection sso_login par defaut."""
    existing = db_session.query(Module).filter(Module.name == "olympe").first()
    if existing is not None:
        db_session.query(Module).filter(Module.id == existing.id).update({"name": "_pytest_hidden_olympe"})
        db_session.commit()
    yield
    if existing is not None:
        db_session.query(Module).filter(Module.id == existing.id).update({"name": "olympe"})
        db_session.commit()


@pytest.mark.parametrize("path", USER_PAGES)
def test_page_accessible_when_logged_in(base_url, make_user, login_as, path):
    user = make_user()
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}{path}", allow_redirects=False)

    assert response.status_code == 200


@pytest.mark.parametrize("path", USER_PAGES)
def test_page_redirects_to_olympe_fqdn_when_desactivated(base_url, make_user, login_as, ensure_olympe_module, path):
    user = make_user(desactivated=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}{path}", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == f"{ensure_olympe_module}/sso/login/?error=2"


@pytest.mark.parametrize("path", USER_PAGES)
def test_page_falls_back_to_sso_login_when_olympe_module_missing(base_url, make_user, login_as, hide_olympe_module, path):
    """Regression : si aucun module "olympe" n'existe en base, ne doit plus planter en 500
    (cf. Utils/verify_login.py, branche desactivated_redirect='olympe_fqdn')."""
    user = make_user(desactivated=True)
    session = login_as(user["username"], user["password"])

    response = session.get(f"{base_url}{path}", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=2"


def test_home_page_redirects_when_not_logged_in(base_url):
    response = requests.get(f"{base_url}/", allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=0"
