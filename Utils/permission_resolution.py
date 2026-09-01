from Utils.Database.permission import Permission
from Utils.Database.group import Group
from Utils.Database.group_member import GroupMember
from Utils.Database.group_permission_override import GroupPermissionOverride

# Colonnes booléennes de Permission qui représentent un droit (hors clé primaire / FK)
_PERMISSION_COLUMN_NAMES = [
    column.name for column in Permission.__table__.columns if column.name not in ("id", "user_token")
]


def _group_ids_for_user(database, user_token):
    return [
        row[0] for row in database.query(GroupMember.group_id).filter(GroupMember.user_token == user_token).all()
    ]


def _winning_group_overrides(database, group_ids):
    """{permission_name: {"value": bool, "groups": [nom, ...], "conflict": bool,
    "dissenting_groups": [nom, ...]}} pour tous les overrides actifs de ces groupes, un seul
    gagnant par permission (priorité la plus haute, égalité tranchée par False) — cf.
    get_effective_permission pour le détail de la règle. `conflict` est vrai dès qu'au moins un
    groupe propose une valeur différente du gagnant (même si sa priorité est plus basse et qu'il
    ne l'emporte donc pas) : sert à avertir l'admin d'une configuration ambiguë."""
    if not group_ids:
        return {}

    rows = database.query(
        GroupPermissionOverride.permission_name, GroupPermissionOverride.value, Group.priority, Group.name
    ).join(Group, Group.id == GroupPermissionOverride.group_id).filter(
        GroupPermissionOverride.group_id.in_(group_ids)
    ).all()

    by_permission = {}
    for permission_name, value, priority, group_name in rows:
        by_permission.setdefault(permission_name, []).append((value, priority, group_name))

    winners = {}
    for permission_name, entries in by_permission.items():
        max_priority = max(priority for _, priority, _ in entries)
        top = [(value, group_name) for value, priority, group_name in entries if priority == max_priority]
        winning_value = False if any(value is False for value, _ in top) else True
        winners[permission_name] = {
            "value": winning_value,
            "groups": [group_name for value, group_name in top if value == winning_value],
            "conflict": any(value != winning_value for value, _, _ in entries),
            "dissenting_groups": sorted({group_name for value, _, group_name in entries if value != winning_value}),
        }
    return winners


def get_effective_permission(database, user_token, permission_name):
    """Resout la valeur effective d'un droit pour un utilisateur, en tenant compte des overrides
    de groupe (cf. Utils/Database/group_permission_override.py). L'admin garde toujours priorité
    absolue (comme avant l'ajout des groupes) : un groupe ne peut jamais bloquer un admin.

    Sans override de groupe sur ce droit, on retombe sur la valeur personnelle de l'utilisateur.
    Avec overrides, seuls ceux des groupes de plus haute priorité comptent ; en cas d'égalité de
    priorité avec des valeurs opposées, False l'emporte (choix produit : le plus restrictif gagne)."""
    user_permission = database.query(Permission).filter(Permission.user_token == user_token).first()
    if user_permission is None:
        return False
    if user_permission.admin:
        return True

    personal_value = bool(getattr(user_permission, permission_name, False))

    group_ids = _group_ids_for_user(database, user_token)
    if not group_ids:
        return personal_value

    overrides = database.query(GroupPermissionOverride.value, Group.priority).join(
        Group, Group.id == GroupPermissionOverride.group_id
    ).filter(
        GroupPermissionOverride.group_id.in_(group_ids),
        GroupPermissionOverride.permission_name == permission_name,
    ).all()

    if not overrides:
        return personal_value

    max_priority = max(priority for _, priority in overrides)
    top_values = [value for value, priority in overrides if priority == max_priority]

    return False if False in top_values else True


def get_group_permission_sources(database, user_token):
    """Pour l'affichage (fiche utilisateur) : quels droits de cet utilisateur sont actuellement
    forcés par un de ses groupes, et par lequel. Retourne {permission_name: {"value": bool,
    "groups": [nom, ...], "conflict": bool, "dissenting_groups": [nom, ...]}} — uniquement les
    droits avec un override actif. N'inclut jamais `admin` (jamais overridable par un groupe,
    cf. edit_group_permission.py)."""
    return _winning_group_overrides(database, _group_ids_for_user(database, user_token))


def get_other_group_overrides_for_group(database, group_id):
    """Pour l'affichage (page d'édition d'un groupe) : parmi les droits que CE groupe force,
    lesquels sont AUSSI forcés par d'autres groupes — indépendamment de tout membre commun, pour
    avertir l'admin d'un conflit potentiel avant même qu'un utilisateur ne se retrouve dans les
    deux groupes. Retourne {permission_name: [{"group": nom, "value": bool, "priority": int}, ...]}
    (uniquement les AUTRES groupes ; vide si aucun autre groupe ne touche à cette permission)."""
    own_permission_names = [
        row[0] for row in database.query(GroupPermissionOverride.permission_name).filter(
            GroupPermissionOverride.group_id == group_id
        ).all()
    ]
    if not own_permission_names:
        return {}

    rows = database.query(
        GroupPermissionOverride.permission_name, GroupPermissionOverride.value, Group.priority, Group.name
    ).join(Group, Group.id == GroupPermissionOverride.group_id).filter(
        GroupPermissionOverride.permission_name.in_(own_permission_names),
        GroupPermissionOverride.group_id != group_id,
    ).all()

    others = {}
    for permission_name, value, priority, group_name in rows:
        others.setdefault(permission_name, []).append({"group": group_name, "value": value, "priority": priority})
    return others


class EffectivePermissionView:
    """Vue en lecture seule de TOUS les droits d'un utilisateur, chaque colonne déjà résolue
    (droit personnel éventuellement forcé par un groupe, même règle que `get_effective_permission`)
    — sert de remplacement direct à l'objet `Permission` passé aux templates/gardes d'UI pour le
    *viewer* connecté (sidebar, boutons conditionnels), en 2-3 requêtes au total plutôt qu'une par
    droit consulté. Ne pas utiliser pour éditer/afficher les valeurs *stockées* d'un utilisateur
    cible (cf. `selected_user_permission` dans show_user.py, qui doit rester la ligne brute)."""

    def __init__(self, values):
        self._values = values

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(name)


def get_effective_permission_view(database, user_token):
    user_permission = database.query(Permission).filter(Permission.user_token == user_token).first()

    if user_permission is not None and user_permission.admin:
        return EffectivePermissionView({name: True for name in _PERMISSION_COLUMN_NAMES})

    values = {
        name: bool(getattr(user_permission, name)) if user_permission is not None else False
        for name in _PERMISSION_COLUMN_NAMES
    }

    winners = _winning_group_overrides(database, _group_ids_for_user(database, user_token))
    for name, info in winners.items():
        values[name] = info["value"]

    return EffectivePermissionView(values)
