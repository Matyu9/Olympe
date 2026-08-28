from flask import redirect, url_for, request, render_template
from Utils.verify_login import login_required

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.group import Group
from Utils.Administration.Modules.module_access import visible_modules_for_user


@login_required(permission='on_off_modules')
def add_group_cogs(database):
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
    modules_info = visible_modules_for_user(database, user_data)
    user_permission = database.query(Permission).filter(Permission.user_token == request.cookies.get('token')).first()

    if request.method == 'GET':
        return render_template('Administration/groups/add_group.html',
                               user_permission=user_permission, user_data=user_data, modules_info=modules_info)
    elif request.method == 'POST':
        group = Group(name=request.form['group_name'], description=request.form.get('group_description'))
        database.add(group)
        database.commit()

        return redirect(url_for('show_groups', group_id=group.id))
