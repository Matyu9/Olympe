import os
from pathlib import Path

from werkzeug.utils import secure_filename

from Utils.Database.user import User

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_FOLDER = PROJECT_ROOT / "static" / "ProfilePicture"


def _picture_path(token, extension):
    # Le code applicatif nomme le fichier via secure_filename(token), qui peut modifier le nom
    # (ex: strip des underscores de tête) : on doit reproduire la même transformation ici.
    return UPLOAD_FOLDER / f"{secure_filename(token)}.{extension}"


def test_disallowed_extension_is_rejected(base_url, make_user, login_as, db_session):
    """Régression sécurité (XSS stocké) : l'extension du fichier envoyé par le client ne doit
    jamais être utilisée telle quelle pour nommer le fichier sauvegardé sur le serveur — un
    upload de .svg/.html pourrait être servi et exécuté depuis le domaine d'Olympe."""
    user = make_user()

    session = login_as(user["username"], user["password"])
    response = session.post(
        f"{base_url}/user_space/",
        files={"profile_picture": ("evil.svg", b"<svg onload=alert(1)></svg>", "image/svg+xml")},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert not _picture_path(user["token"], "svg").exists()

    db_session.expire_all()
    updated = db_session.query(User).filter(User.token == user["token"]).first()
    assert not updated.picture


def test_allowed_extension_is_saved(base_url, make_user, login_as, db_session):
    user = make_user()

    session = login_as(user["username"], user["password"])
    picture_file = _picture_path(user["token"], "png")
    try:
        response = session.post(
            f"{base_url}/user_space/",
            files={"profile_picture": ("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * 32, "image/png")},
            allow_redirects=False,
        )

        assert response.status_code == 302
        assert picture_file.exists()

        db_session.expire_all()
        updated = db_session.query(User).filter(User.token == user["token"]).first()
        assert updated.picture
    finally:
        if picture_file.exists():
            os.remove(picture_file)


def test_filename_without_extension_is_rejected(base_url, make_user, login_as, db_session):
    """Cas limite : un nom de fichier sans '.' ne doit pas planter (IndexError sur l'ancien code)."""
    user = make_user()

    session = login_as(user["username"], user["password"])
    response = session.post(
        f"{base_url}/user_space/",
        files={"profile_picture": ("noextension", b"whatever")},
        allow_redirects=False,
    )

    assert response.status_code == 302

    db_session.expire_all()
    updated = db_session.query(User).filter(User.token == user["token"]).first()
    assert not updated.picture
