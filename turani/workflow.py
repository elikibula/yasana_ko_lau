from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.utils import timezone

from accounts.decorators import is_roko_user
from accounts.models import TuragaProfile, UserProfile

from .models import TNKApprovalAction, TNKReport


ROLE_TURAGA = "turaga_ni_koro"
ROLE_MATA = "mata_ni_tikina"
ROLE_LIULIU = "liuliu_ni_yavusa"
ROLE_ASSISTANT = "assistant_roko"
ROLE_ROKO = "roko_tui"


ACTION_LABELS = {
    TNKApprovalAction.ACTION_SUBMIT: "Submit",
    TNKApprovalAction.ACTION_APPROVE: "Approve",
    TNKApprovalAction.ACTION_RETURN: "Return for correction",
    TNKApprovalAction.ACTION_REJECT: "Reject",
    TNKApprovalAction.ACTION_RECOMMEND: "Recommend approval",
    TNKApprovalAction.ACTION_FINAL_APPROVE: "Final approve",
    TNKApprovalAction.ACTION_ARCHIVE: "Archive",
    TNKApprovalAction.ACTION_COMMENT: "Add comment",
}


def role_for_user(user):
    if not user.is_authenticated:
        return ""
    if user.groups.filter(name__in=["assistant_roko", "assistant_roko_admin"]).exists():
        return ROLE_ASSISTANT
    if is_roko_user(user):
        return ROLE_ROKO

    assigned = getattr(user, "user_profile", None)
    if assigned and assigned.role:
        return assigned.role

    legacy = getattr(user, "turaga_profile", None)
    if legacy and legacy.membership_type == TuragaProfile.TURAGA_NI_YAVUSA:
        return ROLE_LIULIU
    if legacy:
        return legacy.membership_type
    return ""


def role_label(role):
    return {
        ROLE_TURAGA: "Turaga ni Koro",
        ROLE_MATA: "Mata ni Tikina",
        ROLE_LIULIU: "Liuliu ni Yavusa",
        ROLE_ASSISTANT: "Assistant Roko",
        ROLE_ROKO: "Roko Tui",
        UserProfile.ROKO_ADMIN: "Roko Tui",
    }.get(role, role or "User")


def _profile(user):
    return getattr(user, "turaga_profile", None)


def can_view_report(user, report):
    role = role_for_user(user)
    profile = _profile(user)
    if report.owner_id == user.id:
        return True
    if role in {ROLE_ROKO, ROLE_ASSISTANT}:
        return True
    if role == ROLE_MATA and profile and profile.district:
        return report.district.casefold() == profile.district.casefold()
    if role == ROLE_LIULIU and profile:
        if profile.village and report.village.casefold() == profile.village.casefold():
            return True
        if profile.district and report.district.casefold() == profile.district.casefold():
            return True
    return False


def visible_reports_for(user):
    qs = TNKReport.objects.select_related("owner")
    role = role_for_user(user)
    profile = _profile(user)
    if role == ROLE_ROKO or role == ROLE_ASSISTANT:
        return qs
    if role == ROLE_MATA and profile and profile.district:
        return qs.filter(district__iexact=profile.district).exclude(status=TNKReport.STATUS_DRAFT)
    if role == ROLE_LIULIU and profile:
        filters = Q(pk__in=[])
        if profile.village:
            filters |= Q(village__iexact=profile.village)
        if profile.district:
            filters |= Q(district__iexact=profile.district)
        return qs.filter(filters).exclude(status__in=[TNKReport.STATUS_DRAFT, TNKReport.STATUS_SUBMITTED_TO_MATA])
    return qs.filter(owner=user)


def can_edit_report(user, report):
    return (
        report.owner_id == user.id
        and report.status in {TNKReport.STATUS_DRAFT, TNKReport.STATUS_RETURNED_TO_TURAGA}
    )


def allowed_actions(user, report):
    role = role_for_user(user)
    if not can_view_report(user, report):
        return []

    actions = []
    if role == ROLE_MATA and report.status == TNKReport.STATUS_SUBMITTED_TO_MATA:
        actions = [TNKApprovalAction.ACTION_APPROVE, TNKApprovalAction.ACTION_RETURN, TNKApprovalAction.ACTION_REJECT, TNKApprovalAction.ACTION_COMMENT]
    elif role == ROLE_LIULIU and report.status == TNKReport.STATUS_SUBMITTED_TO_LIULIU:
        actions = [TNKApprovalAction.ACTION_APPROVE, TNKApprovalAction.ACTION_RETURN, TNKApprovalAction.ACTION_REJECT, TNKApprovalAction.ACTION_COMMENT]
    elif role == ROLE_ASSISTANT and report.status == TNKReport.STATUS_SUBMITTED_TO_ASSISTANT:
        actions = [TNKApprovalAction.ACTION_RECOMMEND, TNKApprovalAction.ACTION_RETURN, TNKApprovalAction.ACTION_REJECT, TNKApprovalAction.ACTION_COMMENT]
    elif role == ROLE_ROKO:
        if report.status == TNKReport.STATUS_SUBMITTED_TO_ROKO:
            actions = [TNKApprovalAction.ACTION_FINAL_APPROVE, TNKApprovalAction.ACTION_RETURN, TNKApprovalAction.ACTION_REJECT, TNKApprovalAction.ACTION_COMMENT]
        elif report.status in {TNKReport.STATUS_FINAL_APPROVED, TNKReport.STATUS_REJECTED}:
            actions = [TNKApprovalAction.ACTION_ARCHIVE, TNKApprovalAction.ACTION_COMMENT]
    elif report.owner_id == user.id and report.status in {TNKReport.STATUS_SUBMITTED_TO_MATA, TNKReport.STATUS_RETURNED_TO_TURAGA}:
        actions = [TNKApprovalAction.ACTION_COMMENT]

    return [{"type": action, "label": ACTION_LABELS[action]} for action in actions]


def next_status_for_action(user, report, action_type):
    role = role_for_user(user)
    status = report.status

    if action_type == TNKApprovalAction.ACTION_COMMENT:
        return status
    if action_type == TNKApprovalAction.ACTION_SUBMIT and can_edit_report(user, report):
        return TNKReport.STATUS_SUBMITTED_TO_MATA
    if action_type in {TNKApprovalAction.ACTION_RETURN, TNKApprovalAction.ACTION_REJECT}:
        allowed = [item["type"] for item in allowed_actions(user, report)]
        if action_type not in allowed:
            raise ValidationError("This action is not available for the current workflow stage.")
        return TNKReport.STATUS_RETURNED_TO_TURAGA if action_type == TNKApprovalAction.ACTION_RETURN else TNKReport.STATUS_REJECTED
    if action_type == TNKApprovalAction.ACTION_APPROVE and role == ROLE_MATA and status == TNKReport.STATUS_SUBMITTED_TO_MATA:
        return TNKReport.STATUS_SUBMITTED_TO_LIULIU
    if action_type == TNKApprovalAction.ACTION_APPROVE and role == ROLE_LIULIU and status == TNKReport.STATUS_SUBMITTED_TO_LIULIU:
        return TNKReport.STATUS_SUBMITTED_TO_ASSISTANT
    if action_type == TNKApprovalAction.ACTION_RECOMMEND and role == ROLE_ASSISTANT and status == TNKReport.STATUS_SUBMITTED_TO_ASSISTANT:
        return TNKReport.STATUS_SUBMITTED_TO_ROKO
    if action_type == TNKApprovalAction.ACTION_FINAL_APPROVE and role == ROLE_ROKO and status == TNKReport.STATUS_SUBMITTED_TO_ROKO:
        return TNKReport.STATUS_FINAL_APPROVED
    if action_type == TNKApprovalAction.ACTION_ARCHIVE and role == ROLE_ROKO and status in {TNKReport.STATUS_FINAL_APPROVED, TNKReport.STATUS_REJECTED}:
        return TNKReport.STATUS_ARCHIVED
    raise ValidationError("Invalid approval workflow transition.")


def acknowledgement_for(user, action_type):
    name = user.get_full_name().strip() or user.get_username()
    role = role_label(role_for_user(user))
    timestamp = timezone.localtime(timezone.now()).strftime("%d %b %Y %H:%M")
    action_label = ACTION_LABELS.get(action_type, action_type).lower()
    return f"I, {name}, acting as {role}, confirm that I have reviewed this report and performed this action ({action_label}) on {timestamp}."


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_action(request, report, action_type, comment="", to_status=None, from_status=None):
    from_status = from_status if from_status is not None else report.status
    if to_status is None:
        to_status = next_status_for_action(request.user, report, action_type)

    if not can_view_report(request.user, report):
        raise PermissionDenied

    if to_status != report.status:
        report.status = to_status
        if action_type == TNKApprovalAction.ACTION_SUBMIT:
            report.submitted_at = timezone.now()
        report.save(update_fields=["status", "submitted_at", "updated_at"])

    user_name = request.user.get_full_name().strip() or request.user.get_username()
    return TNKApprovalAction.objects.create(
        report=report,
        user=request.user,
        user_full_name=user_name,
        user_role=role_label(role_for_user(request.user)),
        action_type=action_type,
        from_status=from_status,
        to_status=to_status,
        comment=comment,
        digital_acknowledgement=acknowledgement_for(request.user, action_type),
        ip_address=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
