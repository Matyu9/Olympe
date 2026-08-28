import os
from pathlib import Path

from werkzeug.utils import secure_filename

from Utils.Database.user import User

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_FOLDER = PROJECT_ROOT / "static" / "ProfilePicture"


def _picture_path(token, extension):
    return UPLOAD_FOLDER / f"{secure_filename(token)}.{extension}"


def test_disallowed_extension_is_rejected(base_url, make_user, login_as, db_session):
    """Regression securite (XSS stocke) : meme faille que Cogs/User/user_space.py, corrigee
    dans Cogs/Administration/User/show_user.py (edition d'un autre utilisateur cote admin)."""
    actor = make_user()
    target = make_user()
    session = login_as(actor["username"], actor["password"])

    response = session.post(
        f"{base_url}/admin/user/",
        data={"token": target["token"]},
        files={"profile_picture": ("evil.svg", b"<svg onload=alert(1)></svg>", "image/svg+xml")},
        allow_redirects=False,
    )

    assert response.status_code == 302
    assert not _picture_path(target["token"], "svg").exists()

    db_session.expire_all()
    updated = db_session.query(User).filter(User.token == target["token"]).first()
    assert not updated.picture


def test_allowed_extension_is_saved(base_url, make_user, login_as, db_session):
    actor = make_user()
    target = make_user()
    session = login_as(actor["username"], actor["password"])
    picture_file = _picture_path(target["token"], "png")

    try:
        response = session.post(
            f"{base_url}/admin/user/",
            data={"token": target["token"]},
            files={"profile_picture": ("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * 32, "image/png")},
            allow_redirects=False,
        )

        assert response.status_code == 302
        assert picture_file.exists()

        db_session.expire_all()
        updated = db_session.query(User).filter(User.token == target["token"]).first()
        assert updated.picture
    finally:
        if picture_file.exists():
            os.remove(picture_file)
