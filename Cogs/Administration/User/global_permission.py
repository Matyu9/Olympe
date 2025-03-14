from flask import request, redirect, url_for, render_template
from Utils.verify_login import verify_login
from Utils.Administration.User.check_global_permission_edit import check_perm

from Utils.Database.config import Config
from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module


def global_permission_cogs(database):
    if verify_login(database) and verify_login(database) != 'desactivated':
        # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
        modules_info = database.query(Module).all()

        # On récupère les données de l'utilisateur afin de pouvoir l'afficher
        user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

        # On récupère les permissions de l'utilisateur afin de pouvoir afficher les options qui correspondent
        user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

        permission = []
        for i in ['edit_username', 'edit_password', 'edit_email', 'edit_profile_picture', 'edit_a2f']:
            permission.append(database.query(Config.content).filter(Config.name == i).first()[0])

        if not user_permission.allow_edit_username and not user_permission.allow_edit_email and not user_permission.allow_edit_password and not user_permission.allow_edit_profile_picture and not user_permission.allow_edit_A2F and not user_permission.admin:
            return redirect(url_for('home'))

        if request.method == 'POST': # Si la request est de type "POST" on met à jour les permission et on affiche les dernières valeurs
            for i in ['edit_username', 'edit_password', 'edit_email', 'edit_profile_picture', 'edit_A2F']:
                database.query(Permission).update(
                    {
                        i: check_perm(i),
                    }
                )
                database.query(Config).filter(Config.name == i).update(
                    {
                        "content": check_perm(i),
                    }
                )
                database.commit()

            permission = []
            for i in ['edit_username', 'edit_password', 'edit_email', 'edit_profile_picture', 'edit_a2f']:
                permission.append(database.query(Config.content).filter(Config.name == i).first()[0])


        return render_template('Administration/global_permission.html', permission=permission,
                               user_permission=user_permission, modules_info=modules_info, user_data=user_data)

    elif verify_login(database) == "desactivated":
        return redirect(url_for('sso_login', error='2'))
    else:
        return redirect(url_for('sso_login'))
