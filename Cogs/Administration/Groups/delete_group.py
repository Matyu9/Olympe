from Utils.verify_login import login_required
from flask import redirect, url_for, request

from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember
from Utils.Database.module_access import ModuleAccess
from Utils.Database.group_permission_override import GroupPermissionOverride


@login_required(permission='on_off_modules')
def delete_group_cogs(database):
    group_id = request.form['group_id_to_delete']

    # Un groupe supprimé ne doit laisser ni membre, ni accès module, ni override de permission
    # orphelin (pas de contrainte FK en base sur ces colonnes, cf. GroupMember/ModuleAccess).
    database.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    database.query(ModuleAccess).filter(ModuleAccess.group_id == group_id).delete()
    database.query(GroupPermissionOverride).filter(GroupPermissionOverride.group_id == group_id).delete()
    database.query(Group).filter(Group.id == group_id).delete()
    database.commit()

    return redirect(url_for('admin.show_groups'))
