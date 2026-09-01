from flask import redirect, url_for, request, render_template
from Utils.verify_login import login_required

from Utils.Database.user import User
from Utils.Database.group import Group
from Utils.Administration.Modules.module_access import visible_modules_for_user
from Utils.permission_resolution import get_effective_permission_view


@login_required(permission='on_off_modules')
def add_group_cogs(database):
    user_data = database.query(User).filter(User.token == request.cookies.get('token')).first()
    modules_info = visible_modules_for_user(database, user_data)
    user_permission = get_effective_permission_view(database, request.cookies.get('token'))

    if request.method == 'GET':
        return render_template('Administration/groups/add_group.html',
                               user_permission=user_permission, user_data=user_data, modules_info=modules_info)
    elif request.method == 'POST':
        group = Group(
            name=request.form['group_name'],
            description=request.form.get('group_description'),
            priority=int(request.form.get('group_priority') or 0),
        )
        database.add(group)
        database.commit()

        return redirect(url_for('admin.show_groups', group_id=group.id))
