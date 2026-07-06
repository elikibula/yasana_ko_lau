from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import ProfileForm, SignUpForm
from .models import TuragaProfile, UserProfile


GROUP_DASHBOARD_MAP = {
    "turaga_ni_koro": "/turani/dashboard/turaga-ni-koro/",
    "mata_ni_tikina": "/mata-ni-tikina/dashboard/",
    "liuliu_ni_yavusa": "/turaga-ni-yavusa/dashboard/",
    "roko_admin": "/dashboard/admin/",
}

ROLE_GROUP_NAMES = tuple(GROUP_DASHBOARD_MAP)

LEGACY_MEMBERSHIP_GROUP_MAP = {
    TuragaProfile.TURAGA_NI_KORO: "turaga_ni_koro",
    TuragaProfile.MATA_NI_TIKINA: "mata_ni_tikina",
    TuragaProfile.TURAGA_NI_YAVUSA: "liuliu_ni_yavusa",
    TuragaProfile.ROKO: "roko_admin",
}


def sync_user_role(user, group_name):
    from koro.models import Koro
    from tikina.models import Tikina

    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.remove(*Group.objects.filter(name__in=ROLE_GROUP_NAMES).exclude(name=group_name))
    user.groups.add(group)
    legacy_profile = getattr(user, "turaga_profile", None)
    profile_defaults = {"role": group_name}
    if legacy_profile:
        profile_defaults.update(
            {
                "tikina": legacy_profile.district,
                "koro": legacy_profile.village,
                "yavusa": legacy_profile.yavusa,
                "phone": legacy_profile.phone_number,
            }
        )
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    changed = False
    for field, value in profile_defaults.items():
        if value and getattr(user_profile, field) != value:
            setattr(user_profile, field, value)
            changed = True
    if changed:
        user_profile.save()
    if group_name == "turaga_ni_koro" and user_profile.koro:
        Koro.objects.filter(turaga_ni_koro=user_profile).exclude(name__iexact=user_profile.koro).update(turaga_ni_koro=None)
        assigned_koro = Koro.objects.filter(name__iexact=user_profile.koro, tikina__is_active=True).first()
        if assigned_koro and assigned_koro.turaga_ni_koro_id != user_profile.pk:
            assigned_koro.turaga_ni_koro = user_profile
            assigned_koro.save(update_fields=["turaga_ni_koro", "updated_at"])
    if group_name == "mata_ni_tikina" and user_profile.tikina:
        Tikina.objects.filter(mata_ni_tikina=user_profile).exclude(name__iexact=user_profile.tikina).update(mata_ni_tikina=None)
        assigned_tikina = Tikina.objects.filter(name__iexact=user_profile.tikina, is_active=True).first()
        if assigned_tikina and assigned_tikina.mata_ni_tikina_id != user_profile.pk:
            assigned_tikina.mata_ni_tikina = user_profile
            assigned_tikina.save(update_fields=["mata_ni_tikina"])
    return GROUP_DASHBOARD_MAP[group_name]


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        legacy_group = LEGACY_MEMBERSHIP_GROUP_MAP.get(user.turaga_profile.membership_type)
        if legacy_group:
            sync_user_role(user, legacy_group)
        login(request, user)
        messages.success(request, "Your reporting account is ready.")
        return redirect("accounts:dashboard")
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    user_profile, _ = TuragaProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=user_profile)
    if request.method == "POST" and form.is_valid():
        profile = form.save()
        group_name = LEGACY_MEMBERSHIP_GROUP_MAP.get(profile.membership_type)
        if group_name:
            sync_user_role(request.user, group_name)
        messages.success(request, "Your personal details were updated.")
        return redirect("accounts:dashboard")
    return render(request, "accounts/profile_form.html", {"form": form, "profile": user_profile})


@login_required
def dashboard_redirect(request):
    user_profile, _ = TuragaProfile.objects.get_or_create(user=request.user)
    if request.user.is_staff:
        return redirect(sync_user_role(request.user, "roko_admin"))

    assigned_profile = getattr(request.user, "user_profile", None)
    if assigned_profile and assigned_profile.role in GROUP_DASHBOARD_MAP:
        return redirect(sync_user_role(request.user, assigned_profile.role))

    legacy_group = LEGACY_MEMBERSHIP_GROUP_MAP.get(user_profile.membership_type)
    if legacy_group:
        return redirect(sync_user_role(request.user, legacy_group))

    groups = set(request.user.groups.values_list("name", flat=True))
    for group_name in GROUP_DASHBOARD_MAP:
        if group_name in groups:
            return redirect(sync_user_role(request.user, group_name))

    messages.warning(request, "Your reporting role is not assigned yet. Please contact the Provincial Office administrator.")
    return render(request, "dashboard/generic.html", {"legacy_profile": user_profile})
