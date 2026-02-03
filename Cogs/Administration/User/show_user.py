from os import path, remove
from Utils.verify_login import verify_login
from flask import request, render_template, redirect, url_for
from werkzeug.exceptions import BadRequestKeyError
from argon2 import PasswordHasher, exceptions
from werkzeug.utils import secure_filename

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def show_user_cogs(database, upload_path):
    # Vérification de si l'utilisateur est bien connecté et n'a pas un compte désactivé
    if verify_login(database) and verify_login(database) != "desactivated":
        if request.method == 'GET':  # S'il fait une requete de type GET
            # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
            modules_info = database.query(Module).all()

            # On récupère les données de l'utilisateur afin de pouvoir l'afficher
            user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

            # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
            user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

            # Si l'utilisateur n'a pas les permissions, redirection vers la page d'accueil
            if not user_permission.show_specific_account and not user_permission.admin:
                return redirect(url_for('home'))

            # Si l'utilisateur souhaite voir un utilisateur en particulier
            if request.args.get('user_token'):
                # Sélectionne les données et permissions de l'utilisateur souhaité
                selected_user_data = database.query(User).filter(User.token == request.args.get('user_token')).first()
                selected_user_permission = database.query(Permission).filter(Permission.user_token == request.args.get('user_token')).first()

                return render_template('Administration/show_user.html',
                                       multiple_user_info=None,
                                       user_permission=user_permission,
                                       user_data=user_data,
                                       selected_user_info=selected_user_data,
                                       selected_user_permission=selected_user_permission,
                                       modules_info=modules_info)

            else:  # Sinon
                # On sélectionne toute la base de données
                users_data = database.query(User).all()
                return render_template('Administration/show_user.html',
                                       multiple_user_info=users_data,
                                       user_permission=user_permission,
                                       user_data=user_data,
                                       selected_user_info=None,
                                       selected_user_permission=None,
                                       modules_info=modules_info)

        # Si l'utilisateur fait une requete POST
        elif request.method == 'POST':
            # On sélectionne toutes les infos de l'utilisateur
            selected_user_data = database.query(User).filter(User.token == request.form["token"]).first()
            try:
                # On vérifie si l'username a changé
                if request.form['username'] != selected_user_data.username:
                    # Modification de l'username
                    database.query(User).filter(User.token == request.form['token']).update(
                        {"username": request.form["username"]}
                    )
                    database.commit()
            except BadRequestKeyError:
                pass  # Permission refusé

            # On regarde si le mot de passe correspond déjà au Hash qui est dans la base de données,
            try:
                if PasswordHasher().verify(selected_user_data.password, request.form['password1']):
                    pass  # Le MDP ne change pas

            # Le mot de passe ne correspond pas au Hash de la base de données
            except exceptions.VerifyMismatchError:
                if request.form['password1'] != '' and request.form['password1'] == request.form['password2']:
                    # Modification du MDP après vérification que les deux entrées sont strictement égal et pas vides
                    database.query(User).filter(User.token == request.form['token']).update(
                        {"password": PasswordHasher().hash(password=request.form['password1'])}
                    )
                    database.commit()
                else:
                    pass  # L'entrée est vide.
            except BadRequestKeyError:
                pass  # Permission refusé

            try:
                if request.form['email'] != selected_user_data.email:
                    # TODO faire l'algo qui envoie un nouveau code.
                    # Modification de l'email. Modification du code de verif & email_verified mis sur 0 car plus vérifié
                    database.query(User).filter(User.token == request.form['token']).update(
                        {
                            "email": request.form['email'],
                            "email_verification_code": 'reset',
                            "email_verified": 0
                        }
                    )
                    database.commit()
            except BadRequestKeyError:
                pass  # Permission refusé

            try:
                if request.form['theme'] != selected_user_data.theme:
                    # Modification du theme s'il est différent de celui déjà mis.
                    database.query(User).filter(User.token == request.form['token']).update(
                        {"theme": request.form['theme']}
                    )
                    database.commit()
            except BadRequestKeyError:
                pass  # Permission refusé

            # On vérifie si une photo de profile a été envoyé
            if 'profile_picture' in request.files:
                profile_picture = request.files['profile_picture']  # Récupération de la photo
                if profile_picture.filename != '':
                    # Supression des autres photos de profile
                    for extension in ['png', 'jpg', 'jpeg', 'heic']:
                        filepath = path.join(upload_path, f"{request.form['token']}.{extension}")
                        if path.exists(filepath):
                            remove(filepath)

                    # Sauvegarde de la photo
                    profile_picture.save(path.join(upload_path, secure_filename(request.form['token']) + '.' +
                                                   profile_picture.filename.rsplit('.', 1)[1].lower()))
                    # Modification dans la base de données pour pouvoir utiliser la photo.
                    database.query(User).filter(User.token == request.form['token']).update(
                        {"picture": 1}
                    )
                    database.commit()

            return redirect(url_for('show_user', user_token=request.form['token']))
        # Si l'utilisateur utilise un autre moyen d'acceder à la page, un easter egg apparait
        else:
            return redirect('https://i.pinimg.com/originals/cd/0d/76/cd0d7619041d1f141d3e6fea29bb2724.jpg')
    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
