from Utils.Database.module_access import ModuleAccess


def _authorize(session, base_url, module):
    return session.get(
        f"{base_url}/oauth/authorize",
        params={
            "client_id": module.token,
            "response_type": "code",
            "redirect_uri": f"{module.fqdn}/callback",
            "scope": "openid",
        },
        allow_redirects=False,
    )


def test_authorize_denies_user_without_access_on_restricted_module(base_url, make_user, make_module, login_as):
    user = make_user()
    module = make_module(restricted_access=True)
    session = login_as(user["username"], user["password"])

    response = _authorize(session, base_url, module)

    assert response.status_code == 403
    assert module.name in response.text


def test_authorize_allows_user_with_direct_access(base_url, make_user, make_module, login_as, db_session):
    user = make_user()
    module = make_module(restricted_access=True)
    db_session.add(ModuleAccess(module_id=module.id, user_token=user["token"]))
    db_session.commit()

    session = login_as(user["username"], user["password"])
    response = _authorize(session, base_url, module)

    assert response.status_code == 302


def test_authorize_allows_all_users_when_module_not_restricted(base_url, make_user, make_module, login_as):
    user = make_user()
    module = make_module(restricted_access=False)

    session = login_as(user["username"], user["password"])
    response = _authorize(session, base_url, module)

    assert response.status_code == 302
