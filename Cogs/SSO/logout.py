from flask import make_response, redirect, url_for

def sso_logout_cogs(global_domain):
    response = make_response(redirect(url_for('sso.sso_login')))

    # Le `domain=` doit correspondre à celui utilisé au login (Cogs/SSO/login.py) : sans lui,
    # le navigateur crée un cookie vide scopé sur le domaine courant au lieu d'écraser le
    # cookie `.{global_domain}` existant, qui reste donc valide après "déconnexion".
    response.set_cookie('token', "", domain='.' + str(global_domain), expires=0)
    response.set_cookie('validation', "", domain='.' + str(global_domain), expires=0)

    return response