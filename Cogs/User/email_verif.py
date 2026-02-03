from flask import request, render_template, redirect, url_for
from Utils.email_utils import send_verification_email
from Utils.verify_login import verify_login

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def email_verif_cogs(database):
    # Verification si l'utilisateur est connecté
    if not verify_login(database):
        return redirect(url_for('sso_login', error='0'))
    elif verify_login(database) == 'desactivated':  # Si l'utilisateur est connecté mais que son compte est désactivé
        login_url = database.query(Module.fqdn).filter(Module.name == "olympe").first().fqdn
        return redirect(login_url+'/sso/login/?error=2')

    # On récupère les permissions de l'utilisateur
    user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

    # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
    modules_info = database.query(Module).all()

    # On récupère les données de l'utilisateur afin de pouvoir l'afficher
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()


    if request.method == 'POST':  # Si l'utilisateur envoie le formulaire
        code = request.form['mail-code']  # Récupération du code du formulaire.

        if code == user_data.email_verification_code:  # Si le code est bon
            # Sauvegarde de la confirmation dans la base de données
            database.query(User).filter(User.token == request.cookies.get("token")).update(
                    {
                        "email_verification_code": 'checked',
                        "email_verified": 1
                    }
                )
            database.commit()
            return redirect(url_for('user_space'))
        else:  # Sinon redirection vers la page de verification avec une erreur.
            return render_template('User/email-verif.html', error=1, user_permission=user_permission, modules_info=modules_info, user_data=user_data)

    elif request.method == 'GET':  # Si l'utilisateur visite juste la page
        email = send_verification_email(database)  # Envoie du mail avec le code
        if email == "success":
            return render_template('User/email-verif.html', error=0, user_permission=user_permission, modules_info=modules_info, user_data=user_data)
        elif email.startswith("error1"):
            return render_template('User/email-verif.html', error=2, user_permission=user_permission, modules_info=modules_info, user_data=user_data)
        elif email.startswith("error2"):
            return render_template('User/email-verif.html', error=3, user_permission=user_permission, modules_info=modules_info, user_data=user_data)
        elif email == "already_check":
            return redirect(url_for("home"))
