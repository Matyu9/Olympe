from os import path, remove
from Utils.verify_login import login_required
from flask import request, render_template, redirect, url_for
from werkzeug.exceptions import BadRequestKeyError
from argon2 import PasswordHasher, exceptions
from werkzeug.utils import secure_filename

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember
from Utils.Administration.Modules.module_access import visible_modules_for_user
from Utils.permission_resolution import get_group_permission_sources, get_effective_permission_view

# Whitelist stricte des extensions acceptées pour la photo de profil : l'extension du
# fichier envoyé par le client ne doit jamais être utilisée telle quelle (risque d'upload
# d'un .svg/.html menant à du XSS stocké une fois servi depuis le même domaine).
ALLOWED_PICTURE_EXTENSIONS = ('png', 'jpg', 'jpeg', 'heic')


# Note : la vérification de permission (`show_specific_account`) ci-dessous n'est faite que
# pour le GET, pas pour le POST — comportement existant préservé tel quel par ce décorateur
# (qui ne fait que la garde connexion/désactivé), pas une garantie que le POST est protégé.
@login_required()
def show_user_cogs(database, upload_path):
    if request.method == 'GET':  # S'il fait une requete de type GET
        # On récupère les données de l'utilisateur afin de pouvoir l'afficher
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

        # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
        modules_info = visible_modules_for_user(database, user_data)

        # On récupère les permissions effectives de l'utilisateur (droit personnel éventuellement
        # forcé par un groupe, cf. Utils/permission_resolution.py)
        user_permission = get_effective_permission_view(database, request.cookies.get('token'))

        # Si l'utilisateur n'a pas les permissions, redirection vers la page d'accueil
        if not user_permission.show_specific_account and not user_permission.admin:
            return redirect(url_for('user.home'))

        # Si l'utilisateur souhaite voir un utilisateur en particulier
        if request.args.get('user_token'):
            # On ne gère pas son propre compte depuis la vue admin : direction l'espace personnel
            if request.args.get('user_token') == request.cookies.get('token'):
                return redirect(url_for('user.user_space'))

            # Sélectionne les données et permissions de l'utilisateur souhaité
            selected_user_data = database.query(User).filter(User.token == request.args.get('user_token')).first()
            if selected_user_data is None:  # Le token demandé ne correspond à aucun utilisateur
                return redirect(url_for('admin.show_user'))
            selected_user_permission = database.query(Permission).filter(Permission.user_token == request.args.get('user_token')).first()

            # Groupes : résolution manuelle (pas de jointure ORM dans ce codebase, cf. Permission)
            member_rows = database.query(GroupMember).filter(GroupMember.user_token == selected_user_data.token).all()
            selected_user_groups = []
            for member_row in member_rows:
                member_group = database.query(Group).filter(Group.id == member_row.group_id).first()
                if member_group:
                    selected_user_groups.append({"member_id": member_row.id, "group_id": member_group.id, "group_name": member_group.name})
            # Seuls les groupes dont l'utilisateur n'est pas déjà membre apparaissent dans le sélecteur d'ajout
            already_member_group_ids = {group["group_id"] for group in selected_user_groups}
            all_groups = [group for group in database.query(Group).all() if group.id not in already_member_group_ids]

            # Droits actuellement forcés par un des groupes de cet utilisateur (pour désactiver
            # le toggle correspondant et indiquer le groupe responsable, cf. show_user.html)
            selected_user_permission_overrides = get_group_permission_sources(database, selected_user_data.token)

            return render_template('Administration/show_user.html',
                                   multiple_user_info=None,
                                   user_permission=user_permission,
                                   user_data=user_data,
                                   selected_user_info=selected_user_data,
                                   selected_user_permission=selected_user_permission,
                                   selected_user_permission_overrides=selected_user_permission_overrides,
                                   modules_info=modules_info,
                                   selected_user_groups=selected_user_groups,
                                   all_groups=all_groups)

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
        if selected_user_data is None:  # Le token soumis ne correspond à aucun utilisateur
            return redirect(url_for('admin.show_user'))
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
                extension = (
                    profile_picture.filename.rsplit('.', 1)[-1].lower()
                    if '.' in profile_picture.filename else ''
                )

                if extension in ALLOWED_PICTURE_EXTENSIONS:
                    # Supression des autres photos de profile
                    for existing_extension in ALLOWED_PICTURE_EXTENSIONS:
                        filepath = path.join(upload_path, f"{request.form['token']}.{existing_extension}")
                        if path.exists(filepath):
                            remove(filepath)

                    # Sauvegarde de la photo
                    profile_picture.save(path.join(
                        upload_path, secure_filename(request.form['token']) + '.' + extension
                    ))
                    # Modification dans la base de données pour pouvoir utiliser la photo.
                    database.query(User).filter(User.token == request.form['token']).update(
                        {"picture": 1}
                    )
                    database.commit()

        return redirect(url_for('admin.show_user', user_token=request.form['token']))
    # Si l'utilisateur utilise un autre moyen d'acceder à la page, un easter egg apparait
    else:
        return redirect('https://i.pinimg.com/originals/cd/0d/76/cd0d7619041d1f141d3e6fea29bb2724.jpg')
