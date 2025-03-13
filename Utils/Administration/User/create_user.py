from uuid import uuid3, uuid1
from werkzeug.exceptions import BadRequestKeyError
from argon2 import PasswordHasher
from flask import request


def create_user(database):
    token = str(uuid3(uuid1(), str(uuid1())))  # Génération d'un token unique
    hashed_password = PasswordHasher().hash(request.form['password1'])  # Hashage des mots de passe

    # Création de l'utilisateur dans la base de données
    database.exec("""INSERT INTO cantina_administration.user(token, username, password, email, admin, theme) 
    VALUES (%s, %s, %s, %s, %s, %s)""", (token, request.form['username'], hashed_password, request.form['email'],
                                     check_perm('user_admin'), request.form['theme']))

    # Création des permissions de l'utilisateur dans la base de données
    database.exec("""INSERT INTO cantina_administration.permission(user_token, show_log, edit_username, edit_email, 
    edit_password, edit_profile_picture, edit_A2F, edit_theme, show_specific_account, edit_username_admin, 
    edit_email_admin, edit_password_admin, edit_profile_picture_admin, allow_edit_username, allow_edit_email, 
    allow_edit_password, allow_edit_profile_picture, allow_edit_A2F, create_user, delete_account, desactivate_account, 
    edit_permission, show_all_modules, on_off_modules, on_off_maintenance, delete_modules, add_modules, 
    edit_smtp_config, edit_socket_url, edit_url_module, edit_name_module) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s)""",
                  (token, 0, 0, 0,  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    return token


def check_perm(perm_name):
    try:
        return 1 if request.form[perm_name] else 0  # Vérifie si perm_name existe dans le formulaire.
    except BadRequestKeyError:
        return 0
