from Utils.verify_login import login_required
from flask import redirect, url_for, request, render_template

from Utils.Database.user import User
from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember
from Utils.Database.group_permission_override import GroupPermissionOverride
from Utils.Administration.Modules.module_access import visible_modules_for_user
from Utils.permission_resolution import get_effective_permission_view, get_other_group_overrides_for_group


@login_required(permission='on_off_modules')
def show_groups_cogs(database):
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()

    # On récupère les modules afin de pouvoir faire une redirection sur la page via la sidebar
    modules_info = visible_modules_for_user(database, user_data)
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    if request.method == 'POST':
        database.query(Group).filter(Group.id == request.form['group_id']).update(
            {
                "name": request.form['group_name'],
                "description": request.form.get('group_description'),
                "priority": int(request.form.get('group_priority') or 0),
            }
        )
        database.commit()

        return redirect(url_for('admin.show_groups', group_id=request.form['group_id']))

    if request.args.get('group_id'):
        selected_group_info = database.query(Group).filter(Group.id == request.args.get('group_id')).first()
        if selected_group_info is None:
            return redirect(url_for('admin.show_groups'))

        # Résolution manuelle des membres (pas de jointure ORM dans ce codebase, cf. Permission)
        member_rows = database.query(GroupMember).filter(GroupMember.group_id == selected_group_info.id).all()
        selected_group_members = []
        for member_row in member_rows:
            member_user = database.query(User).filter(User.token == member_row.user_token).first()
            if member_user:
                selected_group_members.append({"member_id": member_row.id, "username": member_user.username})
        # Seuls les utilisateurs pas encore membres apparaissent dans le sélecteur d'ajout
        already_member_usernames = {member["username"] for member in selected_group_members}
        all_usernames = [user.username for user in database.query(User).all() if user.username not in already_member_usernames]

        # Overrides actifs sur ce groupe : {permission_name: True/False}. Absence de clé = hérité.
        override_rows = database.query(GroupPermissionOverride).filter(
            GroupPermissionOverride.group_id == selected_group_info.id
        ).all()
        selected_group_permission_overrides = {row.permission_name: row.value for row in override_rows}

        # Droits également forcés par d'autres groupes (indépendamment de tout membre commun) :
        # avertit l'admin d'un conflit potentiel avant même qu'un utilisateur ne soit dans les deux.
        selected_group_other_overrides = get_other_group_overrides_for_group(database, selected_group_info.id)

        return render_template('Administration/show_groups.html',
                               groups_info=None, selected_group_info=selected_group_info,
                               selected_group_members=selected_group_members,
                               selected_group_permission_overrides=selected_group_permission_overrides,
                               selected_group_other_overrides=selected_group_other_overrides,
                               user_permission=user_permission, user_data=user_data, modules_info=modules_info,
                               all_usernames=all_usernames)
    else:
        groups_info = database.query(Group).all()
        return render_template('Administration/show_groups.html',
                               groups_info=groups_info, selected_group_info=None,
                               selected_group_members=None,
                               user_permission=user_permission, user_data=user_data, modules_info=modules_info)
