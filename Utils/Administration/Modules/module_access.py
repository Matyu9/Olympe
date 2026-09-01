from Utils.Database.module_access import ModuleAccess
from Utils.Database.group_member import GroupMember
from Utils.Database.modules import Module
from Utils.permission_resolution import get_effective_permission


def user_can_access_module(database, user, module):
    """Un module non restreint reste ouvert à tous (comportement historique).
    Un module restreint n'est accessible qu'aux utilisateurs/groupes explicitement
    autorisés, sauf pour un admin Olympe ou un titulaire de `show_all_modules`
    (droit personnel ou forcé par un groupe, cf. Utils/permission_resolution.py),
    qui contournent toujours la restriction (même logique que le pattern `x or admin`
    utilisé partout ailleurs)."""
    if not module.restricted_access:
        return True

    if get_effective_permission(database, user.token, "show_all_modules"):
        return True

    direct_access = database.query(ModuleAccess).filter(
        ModuleAccess.module_id == module.id,
        ModuleAccess.user_token == user.token
    ).first()
    if direct_access is not None:
        return True

    user_group_ids = [
        row[0] for row in database.query(GroupMember.group_id).filter(GroupMember.user_token == user.token).all()
    ]
    if not user_group_ids:
        return False

    group_access = database.query(ModuleAccess).filter(
        ModuleAccess.module_id == module.id,
        ModuleAccess.group_id.in_(user_group_ids)
    ).first()
    return group_access is not None


def visible_modules_for_user(database, user):
    """Liste des modules à afficher (accueil, sidebar) pour cet utilisateur : les modules
    restreints auxquels il n'a pas accès sont exclus, pas seulement bloqués à la connexion."""
    return [module for module in database.query(Module).all() if user_can_access_module(database, user, module)]
