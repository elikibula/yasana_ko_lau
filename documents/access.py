ACCESS_GROUP_MAP = {
    "public": None,
    "login": [],
    "koro": ["turaga_ni_koro", "mata_ni_tikina", "liuliu_ni_yavusa", "roko_admin"],
    "tikina": ["mata_ni_tikina", "liuliu_ni_yavusa", "roko_admin"],
    "admin": ["roko_admin"],
}


def user_can_access_document(user, document):
    level = document.access_level
    if level == "public":
        return True
    if not user.is_authenticated:
        return False
    if level == "login":
        return True
    allowed_groups = ACCESS_GROUP_MAP.get(level, [])
    return user.groups.filter(name__in=allowed_groups).exists()
