from Utils.verify_login import login_required
from flask import redirect, url_for, request, render_template
from argon2 import PasswordHasher, exceptions
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.utils import secure_filename
from os import path, remove

from Utils.Database.user import User
from Utils.Database.config import Config
from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember
from Utils.Administration.Modules.module_access import visible_modules_for_user
from Utils.permission_resolution import get_effective_permission_view

# Whitelist stricte des extensions acceptées pour la photo de profil : l'extension du
# fichier envoyé par le client ne doit jamais être utilisée telle quelle (risque d'upload
# d'un .svg/.html menant à du XSS stocké une fois servi depuis le même domaine).
ALLOWED_PICTURE_EXTENSIONS = ('png', 'jpg', 'jpeg', 'heic')


@login_required(desactivated_redirect='olympe_fqdn')
def user_space_cogs(database, upload_path):
    # Récupération des données de l'utilisateur
    user_information = database.query(User).filter(User.token == request.cookies.get('token')).first()

    if request.method == 'GET':
        # Récupération des permissions effectives de l'utilisateur (droit personnel éventuellement
        # forcé par un groupe, cf. Utils/permission_resolution.py)
        user_permission = get_effective_permission_view(database, request.cookies.get('token'))
        # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
        modules_info = visible_modules_for_user(database, user_information)
        # On récupère les permissions générales
        general_permission = {config.name: int(config.content)   for config in database.query(Config).filter(Config.name.startswith('edit_')).all()} # in {"edit_username":1, "edit_password":1, "edit_email":1, "edit_profile_picture":1, "edit_a2f":1}

        # Groupes de l'utilisateur, en lecture seule (résolution manuelle, cf. Permission)
        member_rows = database.query(GroupMember).filter(GroupMember.user_token == user_information.token).all()
        user_groups = []
        for member_row in member_rows:
            member_group = database.query(Group).filter(Group.id == member_row.group_id).first()
            if member_group:
                user_groups.append(member_group.name)

        return render_template('User/user_space.html', user_information=user_information,
                               user_permission=user_permission, modules_info=modules_info, general_permission=general_permission,
                               user_groups=user_groups)

    elif request.method == 'POST':
        try:
            if request.form['username'] != user_information.username:
                # Modification de l'username après vérification qu'il ai changé
                database.query(User).filter(User.token == request.cookies.get("token")).update(
                    {"username": request.form["username"]}
                )
                database.commit()
        except BadRequestKeyError:
            pass  # Permission refusé

        try:
            if PasswordHasher().verify(user_information.password, request.form['password1']):
                pass  # Le MDP ne change pas.
        except exceptions.VerifyMismatchError:
            if request.form['password1'] != '' and request.form['password1'] == request.form['password2']:
                # Modification du MDP après vérification que les deux entrées sont strictement égal et pas vides
                database.query(User).filter(User.token == request.cookies.get("token")).update(
                    {"password": PasswordHasher().hash(password=request.form['password1'])}
                )
                database.commit()
            else:
                pass  # L'entrée est vide ou les deux mdp ne correspondent pas.
        except BadRequestKeyError:
            pass  # Permission refusé

        try:
            if request.form['email'] != user_information.email:
                # Modification de l'email. Modification du code de verif et email_verified mis sur 0 car plus vérifié
                database.query(User).filter(User.token == request.cookies.get("token")).update(
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
            if request.form['theme'] != user_information.theme:
                # Modification du theme s'il est différent de celui déjà mis.
                database.query(User).filter(User.token == request.cookies.get("token")).update(
                    {"theme": request.form['theme']}
                )
                database.commit()
        except BadRequestKeyError:
            pass  # Permission refusé

        if 'profile_picture' in request.files:  # Si une photo de profil a été envoyé
            profile_picture = request.files['profile_picture']  # Récupération de la photo
            if profile_picture.filename != '':
                extension = (
                    profile_picture.filename.rsplit('.', 1)[-1].lower()
                    if '.' in profile_picture.filename else ''
                )

                if extension in ALLOWED_PICTURE_EXTENSIONS:
                    # Supression des autres photos de profil
                    for existing_extension in ALLOWED_PICTURE_EXTENSIONS:
                        filepath = path.join(upload_path, f"{request.cookies.get('token')}.{existing_extension}")
                        if path.exists(filepath):
                            remove(filepath)

                    # Sauvegarde de la photo
                    profile_picture.save(path.join(
                        upload_path, secure_filename(request.cookies.get('token')) + '.' + extension
                    ))
                    # Modification dans la base de données pour pouvoir utiliser la photo.
                    database.query(User).filter(User.token == request.cookies.get("token")).update(
                        {"picture": 1}
                    )
                    database.commit()

        return redirect(url_for('user.user_space'))

    return None
        