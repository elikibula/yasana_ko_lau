from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .decorators import is_roko_user
from .models import TuragaProfile


REPORT_ROLE_LABELS = {
    TuragaProfile.TURAGA_NI_KORO: "Turaga ni Koro",
    TuragaProfile.MATA_NI_TIKINA: "Mata ni Tikina",
    TuragaProfile.TURAGA_NI_YAVUSA: "Turaga ni Yavusa",
}


def resolve_report_owner(request, role, create_url_name):
    if not is_roko_user(request.user):
        profile, _ = TuragaProfile.objects.get_or_create(user=request.user)
        return profile, None

    owner_id = request.GET.get("owner") or request.POST.get("owner")
    profiles = (
        TuragaProfile.objects.select_related("user")
        .filter(membership_type=role, user__is_active=True)
        .order_by("user__first_name", "user__last_name", "user__username")
    )

    if owner_id:
        profile = get_object_or_404(profiles, user_id=owner_id)
        return profile, None

    response = render(
        request,
        "accounts/report_owner_select.html",
        {
            "profiles": profiles,
            "role": role,
            "role_label": REPORT_ROLE_LABELS.get(role, "Reporter"),
            "create_url": reverse(create_url_name),
        },
    )
    return None, response
