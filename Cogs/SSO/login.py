from flask import request, render_template, redirect, url_for, make_response
from Utils.verify_login import verify_login, verify_A2F
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from werkzeug.exceptions import BadRequestKeyError

from Utils.Database.user import User
from Utils.Database.config import Config
from Utils.Database.modules import Module
from Utils.Administration.Modules.module_access import user_can_access_module


def _safe_next_url():
    # Anti open-redirect : seule une reprise vers le flow OIDC est autorisée
    next_url = request.args.get('next')
    if next_url and next_url.startswith('/oauth/authorize?'):
        return next_url
    return None


def sso_login_cogs(database, error, global_domain):
    if request.method == 'POST':  # Si l'utilisateur à remplir le formulaire
        username = request.form['username']  # Sauvegarde du nom d'utilisateur
        password = request.form['password']  # Sauvegarde du mot de passe

        try:
            dfa_code = request.form['a2f-code']  # Sauvegarde du code d'A2F si l'utilisateur en à remplir un
        except BadRequestKeyError:
            dfa_code = None

        # Séléction des données requises pour valider la connexion.
        row = database.query(User).filter(User.username == username).first()
        validation_code = database.query(Config.content).filter(Config.name == "secret_token").scalar()
        domain_to_redirect = database.query(Module).filter(Module.name == request.args.get('modules')).first()

        if row is None:  # Si aucune correspondance, redirect vers la page de login avec le message d'erreur n°1
            return redirect(url_for('sso_login', error='1'))

        try:
            PasswordHasher().verify(row.password, password)  # Verification de la correspondance du MDP

            if row.A2F and dfa_code is None:  # Si l'A2F est activée, mais qu'aucun code n'est fournis
                return render_template('SSO/2FA-Verif.html', password=password, username=username)

            elif not row.A2F or verify_A2F(row.A2F_secret):  # Si l'A2F n'est pas activé ou que le code est correcte
                next_url = _safe_next_url()
                if next_url is not None:
                    response = make_response(redirect(next_url, code=302))
                elif domain_to_redirect is None:
                    url = url_for('home')
                    response = make_response(redirect(url, code=302))
                elif not user_can_access_module(database, row, domain_to_redirect):
                    url = url_for('home', module_access_denied='1', module_name=domain_to_redirect.name)
                    response = make_response(redirect(url, code=302))
                else:
                    response = make_response(redirect(domain_to_redirect.fqdn, code=302))

                # Création des cookies de vérification d'authentification
                response.set_cookie('token', row.token, domain='.'+str(global_domain))
                response.set_cookie('validation', validation_code, domain='.'+str(global_domain))
                return response
            else:  # Dans tous les autres cas
                return redirect(url_for('sso_login', error='1'))

        except VerifyMismatchError:  # Si le MDP ne correspond pas, redirect vers le login avec le message d'erreur n°1
            return redirect(url_for('sso_login', error='1'))

    elif request.method == 'GET':  # Si l'utilisateur consulte la page
        # Si l'utilisateur est déjà connecté et que son compte n'est pas désactivé, redirection auto
        if verify_login(database) and verify_login(database) != 'desactivated':
            next_url = _safe_next_url()
            if next_url is not None:
                return redirect(next_url, code=302)

            domain_to_redirect = database.query(Module).filter(Module.name == request.args.get('modules')).first()

            if domain_to_redirect is None:
                return redirect(url_for('home'))
            else:
                current_user = database.query(User).filter(User.token == request.cookies.get('token')).first()
                if not user_can_access_module(database, current_user, domain_to_redirect):
                    return redirect(url_for('home', module_access_denied='1', module_name=domain_to_redirect.name))
                return redirect(domain_to_redirect.fqdn, code=302)

        print(verify_login(database))

        # Sinon, affichage de la page de connexion
        return render_template('SSO/login.html', error=error)
    else:
        return None
