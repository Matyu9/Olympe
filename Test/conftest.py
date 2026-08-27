import sys
import json
from pathlib import Path
from uuid import uuid4

import pytest
import requests
from argon2 import PasswordHasher
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Le serveur (app.py) tourne comme process séparé : ces tests lui envoient de vraies
# requêtes HTTP, ils n'importent jamais app.py. Il faut donc ajouter la racine du projet
# au sys.path nous-mêmes pour pouvoir importer les modèles SQLAlchemy (Utils.Database.*)
# et écrire/nettoyer directement le compte de test dans la base.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module
from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember
from Utils.Database.module_access import ModuleAccess

TEST_USERNAME_PREFIX = "_pytest_"
TEST_PASSWORD = "Pytest-Test-Password-1!"


def _load_config():
    with open(PROJECT_ROOT / "config.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def config():
    return _load_config()


@pytest.fixture(scope="session")
def base_url(config):
    return f"http://{config['modules'][0]['global_domain']}"


@pytest.fixture(scope="session", autouse=True)
def ensure_server_running(base_url):
    """Échoue tôt et clairement si `python app.py` n'a pas été lancé avant les tests."""
    try:
        requests.get(f"{base_url}/sso/login/", timeout=3)
    except requests.exceptions.ConnectionError:
        pytest.fail(
            f"Impossible de joindre {base_url} — lance le serveur avec `python app.py` "
            "dans un autre terminal avant de lancer les tests.",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def db_engine(config):
    db = config["database"][0]
    engine = create_engine(
        f"mysql+pymysql://{db['username']}:{db['password']}@{db['address']}:{db['port']}/"
    )
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


def _delete_user(db_session, token):
    db_session.query(Permission).filter(Permission.user_token == token).delete()
    db_session.query(User).filter(User.token == token).delete()
    db_session.commit()


@pytest.fixture()
def make_user(db_session):
    """Factory de compte de test : make_user(admin=True, desactivated=True, ...perm kwargs).
    Chaque compte créé est automatiquement supprimé (User + Permission) à la fin du test."""
    created_tokens = []

    def _make_user(desactivated=False, **permission_kwargs):
        token = f"{TEST_USERNAME_PREFIX}{uuid4()}"
        username = token  # unique, préfixé, facilement identifiable/nettoyable

        db_session.add(User(
            token=token,
            username=username,
            password=PasswordHasher().hash(TEST_PASSWORD),
            email=f"{token}@example.invalid",
            desactivated=desactivated,
        ))
        db_session.add(Permission(user_token=token, **permission_kwargs))
        db_session.commit()

        created_tokens.append(token)
        return {"token": token, "username": username, "password": TEST_PASSWORD}

    yield _make_user

    for token in created_tokens:
        _delete_user(db_session, token)


@pytest.fixture(autouse=True)
def _cleanup_stale_test_users(db_session):
    """Filet de sécurité : si un run précédent a planté avant son teardown, on nettoie
    les comptes _pytest_* restants avant de commencer un nouveau test."""
    stale = db_session.query(User.token).filter(User.username.like(f"{TEST_USERNAME_PREFIX}%")).all()
    for (token,) in stale:
        _delete_user(db_session, token)
    yield


@pytest.fixture()
def make_module(db_session):
    """Factory de module de test : make_module(restricted_access=True).
    Chaque module créé (+ ses ModuleAccess éventuels) est nettoyé à la fin du test."""
    created_tokens = []

    def _make_module(restricted_access=False):
        token = f"{TEST_USERNAME_PREFIX}{uuid4()}"
        module = Module(
            token=token,
            name=f"{token}_module",
            fqdn=f"https://{token}.example.invalid",
            restricted_access=restricted_access,
        )
        db_session.add(module)
        db_session.commit()

        created_tokens.append(token)
        return module

    yield _make_module

    for token in created_tokens:
        module = db_session.query(Module).filter(Module.token == token).first()
        if module is not None:
            db_session.query(ModuleAccess).filter(ModuleAccess.module_id == module.id).delete()
            db_session.query(Module).filter(Module.token == token).delete()
    db_session.commit()


@pytest.fixture()
def make_group(db_session):
    """Factory de groupe de test : make_group() -> Group.
    Chaque groupe créé (+ ses membres et accès module) est nettoyé à la fin du test."""
    created_ids = []

    def _make_group():
        group = Group(name=f"{TEST_USERNAME_PREFIX}group_{uuid4()}")
        db_session.add(group)
        db_session.commit()

        created_ids.append(group.id)
        return group

    yield _make_group

    for group_id in created_ids:
        db_session.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
        db_session.query(ModuleAccess).filter(ModuleAccess.group_id == group_id).delete()
        db_session.query(Group).filter(Group.id == group_id).delete()
    db_session.commit()


@pytest.fixture()
def login_as(base_url):
    """login_as(username, password) -> requests.Session authentifiée (cookies posés)."""

    def _login_as(username, password):
        session = requests.Session()
        session.post(
            f"{base_url}/sso/login/",
            data={"username": username, "password": password},
            allow_redirects=False,
        )
        return session

    return _login_as
