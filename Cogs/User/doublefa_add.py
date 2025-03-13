from pyotp import random_base32, totp
from flask import request, render_template, redirect, url_for
from Utils.verify_login import verify_A2F, verify_login

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def doubleFA_add_cogs(database):
    # Verification si l'utilisateur est connecté
    if not verify_login(database):
        return redirect(url_for('sso_login', error='0'))
    elif verify_login(database) == 'desactivated':  # Si l'utilisateur est connecté, mais que son compte est désactivé
        login_url = database.query(Module.fqdn).filter(Module.name == "olympe").first().fqdn
        return redirect(login_url+'/sso/login/?error=2')

    # On récupère les permissions de l'utilisateur
    user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

    # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
    modules_info = database.query(Module).all()

    # On récupère les données l'utilisateur afin de pouvoir l'afficher
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

    if request.method == 'POST':  # Si l'utilisateur valide le formulaire
        if verify_A2F(user_data.A2F_secret):  # Vérification réussie du code via la base de donnée
            database.query(User).filter(User.token == request.cookies.get("token")).update(
                {"A2F": 1}
            ) # Activation de l'A2F pour l'authentification
            database.commit()
            return redirect(url_for('user_space'))
        else:  # Vérification ratée du code
            # Génération du lien avec la chaine de caractère lié à l'utilisateur.
            totp_auth = totp.TOTP(user_data.A2F_secret).provisioning_uri(
                name='Cantina Olympe',
                issuer_name=user_data.username
            )
            return render_template('User/2FA-add.html', totp_auth=totp_auth,
                                   error=1, user_permission=user_permission, modules_info=modules_info, user_data=user_data)

    elif request.method == 'GET':  # Si l'utilisateur consulte la page du formulaire.
        # Si l'utilisateur à déjà l'A2F d'activé, redirection vers la page d'accueil.
        if user_data.A2F:
            return redirect(url_for('home'))

        # Si aucune chaine de caractère n'avait été généré
        if user_data.A2F_secret is None:
            database.query(User).filter(User.token == request.cookies.get("token")).update(
                {"A2F_secret": random_base32()}
            )
            database.commit()

        # Génération du lien avec la chaine de caractère lié à l'utilisateur.
        totp_auth = totp.TOTP(user_data.A2F_secret).provisioning_uri(
            name='Cantina Olympe',
            issuer_name=user_data.username
        )

        return render_template('User/2FA-add.html', totp_auth=totp_auth,
                               error=0, user_permission=user_permission, modules_info=modules_info, user_data=user_data)
