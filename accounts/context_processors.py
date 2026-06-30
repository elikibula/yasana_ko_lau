from .models import TuragaProfile


ROLE_LABELS = {
    "turaga_ni_koro": "Turaga ni Koro",
    "mata_ni_tikina": "Mata ni Tikina",
    "liuliu_ni_yavusa": "Liuliu ni Yavusa",
    "roko_admin": "Roko Admin",
}

ROLE_BADGE_CLASSES = {
    "turaga_ni_koro": "bg-green-700 text-white",
    "mata_ni_tikina": "bg-lau-ocean text-white",
    "liuliu_ni_yavusa": "bg-lau-earth text-white",
    "roko_admin": "bg-lau-navy text-lau-gold border border-lau-gold",
}


def membership(request):
    if not request.user.is_authenticated:
        return {"membership_type": "", "is_roko_user": False, "current_role_group": "", "current_role_label": ""}
    profile, _ = TuragaProfile.objects.get_or_create(user=request.user)
    role_group = ""
    group_names = set(request.user.groups.values_list("name", flat=True))
    for candidate in ROLE_LABELS:
        if candidate in group_names:
            role_group = candidate
            break
    return {
        "membership_type": profile.membership_type,
        "membership_label": profile.get_membership_type_display(),
        "is_roko_user": request.user.is_staff or role_group == "roko_admin" or profile.membership_type == TuragaProfile.ROKO,
        "current_role_group": role_group,
        "current_role_label": ROLE_LABELS.get(role_group, "Role pending"),
        "current_role_badge_class": ROLE_BADGE_CLASSES.get(role_group, "bg-gray-700 text-white"),
    }
