from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import TuragaProfile


def is_roko_user(user):
    if not user.is_authenticated:
        return False
    profile, _ = TuragaProfile.objects.get_or_create(user=user)
    return (
        user.is_staff
        or profile.membership_type == TuragaProfile.ROKO
        or user.groups.filter(name="roko_admin").exists()
    )


def membership_required(*allowed_roles, allow_roko=False):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            profile, _ = TuragaProfile.objects.get_or_create(user=request.user)
            is_roko = is_roko_user(request.user)
            if not profile.is_complete and not (allow_roko and is_roko):
                messages.warning(request, "Complete your account details before continuing.")
                return redirect("accounts:profile")
            if profile.membership_type not in allowed_roles and not (allow_roko and is_roko):
                messages.error(request, "That reporting area is not available for your account type.")
                return redirect("accounts:dashboard")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
