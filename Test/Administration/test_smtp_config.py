import requests

from Utils.Database.config import Config, set_config

SMTP_CONFIG_URL = "/admin/smtp/config/"


def test_redirects_when_not_logged_in(base_url):
    response = requests.post(f"{base_url}{SMTP_CONFIG_URL}", data={"SMTP_URL": "x"}, allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/sso/login/?error=0"  # via le hook global verify_maintenance


def test_redirects_when_missing_permission(base_url, make_user, login_as):
    user = make_user()  # edit_smtp_config=False par défaut

    session = login_as(user["username"], user["password"])
    response = session.post(f"{base_url}{SMTP_CONFIG_URL}", data={"SMTP_URL": "x"}, allow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_post_updates_whitelisted_smtp_key(base_url, make_user, login_as, db_session):
    user = make_user(edit_smtp_config=True)
    original = db_session.query(Config.content).filter(Config.name == "SMTP_URL").scalar()

    session = login_as(user["username"], user["password"])
    try:
        response = session.post(
            f"{base_url}{SMTP_CONFIG_URL}",
            data={"SMTP_URL": "smtp.example.invalid"},
            allow_redirects=False,
        )

        assert response.status_code == 302

        db_session.expire_all()
        assert db_session.query(Config.content).filter(Config.name == "SMTP_URL").scalar() == "smtp.example.invalid"
    finally:
        set_config(db_session, "SMTP_URL", original or "")
        db_session.commit()


def test_post_ignores_non_smtp_fields(base_url, make_user, login_as, db_session):
    """Régression sécurité (mass-assignment) : seules les clés de SMTP_KEYS doivent pouvoir être
    écrites par ce formulaire — un champ arbitraire comme `secret_token` (utilisé par le cookie
    de validation cross-domaine) ne doit jamais être modifiable depuis ici."""
    user = make_user(edit_smtp_config=True)
    original_secret = db_session.query(Config.content).filter(Config.name == "secret_token").scalar()
    original_smtp_url = db_session.query(Config.content).filter(Config.name == "SMTP_URL").scalar()

    session = login_as(user["username"], user["password"])
    try:
        response = session.post(
            f"{base_url}{SMTP_CONFIG_URL}",
            data={
                "SMTP_URL": "smtp.example.invalid",
                "secret_token": "hijacked-value",
            },
            allow_redirects=False,
        )

        assert response.status_code == 302

        db_session.expire_all()
        assert db_session.query(Config.content).filter(Config.name == "secret_token").scalar() == original_secret
        # La clé whitelistée, elle, doit bien avoir été appliquée.
        assert db_session.query(Config.content).filter(Config.name == "SMTP_URL").scalar() == "smtp.example.invalid"
    finally:
        set_config(db_session, "SMTP_URL", original_smtp_url or "")
        db_session.commit()
