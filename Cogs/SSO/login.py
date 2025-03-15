from flask import request, render_template, redirect, url_for, make_response
from Utils.verify_login import verify_login, verify_A2F
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from werkzeug.exceptions import BadRequestKeyError

from Utils.Database.user import User
from Utils.Database.config import Config
from Utils.Database.modules import Module


def sso_login_cogs(database, error, global_domain):
    if request.method == 'POST':  # Si l'utilisateur à remplir le formulaire
        username = request.form['username']  # Sauvegarde du nom d'utilisateur
        password = request.form['password']  # Sauvegarde du mot de passe

        try:
            dfa_code = request.form['a2f-code']  # Sauvegarde du code d'A2F si l'utilisateur en à remplir un
        except BadRequestKeyError:
            dfa_code = None

        # Séléction des données requises pour valider la connexion.
        row = database.query(User.password, User.token, User.A2F).filter(User.username == username).first()
        validation_code = database.query(Config.content).filter(Config.name == "secret_token").scalar()
        domain_to_redirect = database.query(Module.fqdn).filter(Module.name == request.args.get('modules')).first()

        if row is None:  # Si aucune correspondance, redirect vers la page de login avec le message d'erreur n°1
            return redirect(url_for('sso_login', error='1'))

        try:
            PasswordHasher().verify(row[0], password)  # Verification de la correspondance du MDP
            if row[2] and dfa_code is None:  # Si l'A2F est activée, mais qu'aucun code n'est fournis
                return render_template('SSO/2FA-Verif.html', password=password, username=username)

            elif not row[2] or verify_A2F(database):  # Si l'A2F n'est pas activé ou que le code est correcte
                if domain_to_redirect is None:
                    response = make_response(redirect(url_for('home')))
                else:
                    response = make_response(redirect(domain_to_redirect, code=302))

                # Création des cookies de vérification d'authentification
                response.set_cookie('token', row[1], domain='.'+str(global_domain))
                response.set_cookie('validation', validation_code[0], domain='.'+str(global_domain))
                return response
            else:  # Dans tous les autres cas
                return redirect(url_for('sso_login', error='1'))

        except VerifyMismatchError:  # Si le MDP ne correspond pas, redirect vers le login avec le message d'erreur n°1
            return redirect(url_for('sso_login', error='1'))

    elif request.method == 'GET':  # Si l'utilisateur consulte la page
        # Si l'utilisateur est déjà connecté et que son compte n'est pas désactivé, redirection auto
        if verify_login(database) and verify_login(database) != 'desactivated':
            domain_to_redirect = database.query(Module.fqdn).filter(Module.name == request.args.get('modules')).first()

            if domain_to_redirect is None:
                return redirect(url_for('home'))
            else:
                return redirect(domain_to_redirect, code=302)

        # Sinon, affichage de la page de connexion
        return render_template('SSO/login.html', error=error)
