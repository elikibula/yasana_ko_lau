from collections import OrderedDict

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import is_roko_user, membership_required
from accounts.models import TuragaProfile
from accounts.reporting import resolve_report_owner
from common.pdf_exports import report_pdf_response
from turani.forms import ApprovalActionForm
from turani.analytics import tnk_dashboard_analysis
from turani.models import Business, HousingCount, PopulationAgeGroup, TNKReport

from .analytics import tny_dashboard_analysis
from .forms import SignatureFormSet, TNY_FIJIAN_INLINE_LABELS, TNY_FORMSET_TITLES, TNY_SECTIONS, TNYReportForm
from .models import Signature, TNYApprovalAction, TNYReport


REPORT_PREFETCHES = ("signatures",)


DETAIL_LABELS_BY_MODEL = {
    SignatureFormSet.model.__name__: {
        **TNY_FIJIAN_INLINE_LABELS.get(SignatureFormSet.model.__name__, {}),
        **(getattr(SignatureFormSet.form._meta, "labels", None) or {}),
    }
}


ACTION_LABELS = {
    TNYApprovalAction.ACTION_APPROVE: "Vakadonuya",
    TNYApprovalAction.ACTION_RETURN: "Vakalesuya me Vakadodonutaki",
    TNYApprovalAction.ACTION_REJECT: "Cata",
    TNYApprovalAction.ACTION_COMMENT: "Vakamacala",
}


def reports_for(user):
    qs = TNYReport.objects.select_related("owner").prefetch_related(*REPORT_PREFETCHES)
    return qs if is_roko_user(user) else qs.filter(owner=user)


def _get_tny_formsets(data=None, instance=None, initial_seeds=False):
    kwargs = {"instance": instance}
    if data is not None and "signatures-TOTAL_FORMS" in data:
        kwargs["data"] = data
    formsets = OrderedDict([("signatures", SignatureFormSet(**kwargs, prefix="signatures"))])
    if initial_seeds and instance is None and data is None:
        formsets["signatures"] = SignatureFormSet(prefix="signatures", initial=[{"role": value} for value, _ in Signature.ROLE_CHOICES])
    return formsets


def _profile_report_defaults(user):
    profile, _ = TuragaProfile.objects.get_or_create(user=user)
    return profile, {
        "owner": user,
        "full_name": profile.full_name,
        "phone_number": profile.phone_number,
        "email": user.email,
        "tokatoka": profile.tokatoka,
        "mataqali": profile.mataqali,
        "yavusa": profile.yavusa,
        "vanua": profile.vanua,
        "koro": profile.village,
        "tikina": profile.district,
    }


def _with_missing_defaults(post_data, report):
    data = post_data.copy()
    for field in report._meta.fields:
        if field.name in {"id", "owner", "created_at", "updated_at"}:
            continue
        if field.name not in data:
            value = getattr(report, field.name)
            data[field.name] = "" if value is None else str(value)
    return data


def _bound_formsets(formsets):
    return [formset for formset in formsets.values() if formset.is_bound]


def _form_fields(form, names):
    return [form[name] for name in names if name in form.fields]


def _report_form_blocks(form, formsets):
    blocks = []
    for title, names in TNY_SECTIONS:
        blocks.append({"type": "chapter", "title": title})
        blocks.append({"type": "section", "title": title, "fields": _form_fields(form, names)})
    blocks.append({"type": "formset", "key": "signatures", "title": TNY_FORMSET_TITLES["signatures"], "formset": formsets["signatures"]})
    return blocks


def _field_label(field, labels=None):
    return (labels or {}).get(field.name, field.verbose_name.title())


def _field_value(obj, field, labels=None):
    value = getattr(obj, field.name)
    if field.choices:
        value = getattr(obj, f"get_{field.name}_display")()
    elif isinstance(value, bool):
        value = "Io" if value else "Sega"
    elif value in (None, ""):
        value = "-"
    return _field_label(field, labels), value


def _detail_sections(report):
    labels = TNYReportForm.Meta.labels
    return [
        (title, [_field_value(report, report._meta.get_field(name), labels) for name in names])
        for title, names in TNY_SECTIONS
    ]


def _model_rows(items):
    rows = []
    for item in items:
        labels = DETAIL_LABELS_BY_MODEL.get(item._meta.model.__name__, {})
        rows.append([_field_value(item, field, labels) for field in item._meta.fields if field.name not in {"id", "report"}])
    return rows


def can_edit_report(user, report):
    return report.owner_id == user.id and report.status in {
        TNYReport.STATUS_DRAFT,
        TNYReport.STATUS_RETURNED_BY_ROKO,
    }


def can_export_report(report):
    return report.status == TNYReport.STATUS_APPROVED_BY_ROKO


def workflow_actions_for(user, report):
    if not is_roko_user(user):
        return []
    if report.status == TNYReport.STATUS_SUBMITTED_TO_ROKO:
        actions = [
            TNYApprovalAction.ACTION_APPROVE,
            TNYApprovalAction.ACTION_RETURN,
            TNYApprovalAction.ACTION_REJECT,
            TNYApprovalAction.ACTION_COMMENT,
        ]
    else:
        actions = [TNYApprovalAction.ACTION_COMMENT] if report.status != TNYReport.STATUS_DRAFT else []
    return [{"type": action, "label": ACTION_LABELS[action]} for action in actions]


def next_status_for_action(report, action_type):
    if action_type == TNYApprovalAction.ACTION_COMMENT:
        return report.status
    if report.status != TNYReport.STATUS_SUBMITTED_TO_ROKO:
        raise ValidationError("This report is not waiting for Roko Tui approval.")
    if action_type == TNYApprovalAction.ACTION_APPROVE:
        return TNYReport.STATUS_APPROVED_BY_ROKO
    if action_type == TNYApprovalAction.ACTION_RETURN:
        return TNYReport.STATUS_RETURNED_BY_ROKO
    if action_type == TNYApprovalAction.ACTION_REJECT:
        return TNYReport.STATUS_REJECTED_BY_ROKO
    raise ValidationError("Invalid approval workflow action.")


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_approval_action(request, report, action_type, comment="", to_status=None, from_status=None):
    if action_type != TNYApprovalAction.ACTION_SUBMIT and not is_roko_user(request.user):
        raise PermissionDenied
    from_status = from_status if from_status is not None else report.status
    to_status = to_status if to_status is not None else next_status_for_action(report, action_type)
    if to_status != report.status:
        report.status = to_status
        report.save(update_fields=["status", "updated_at"])
    user_name = request.user.get_full_name().strip() or request.user.get_username()
    action_label = dict(TNYApprovalAction.ACTION_CHOICES).get(action_type, action_type).lower()
    user_role = "Roko Tui" if is_roko_user(request.user) else "Liuliu ni Yavusa"
    acknowledgement = f"I, {user_name}, acting as {user_role}, confirm that I reviewed this report and performed this action ({action_label}) on {timezone.localtime(timezone.now()).strftime('%d %b %Y %H:%M')}."
    return TNYApprovalAction.objects.create(
        report=report,
        user=request.user,
        user_full_name=user_name,
        user_role=user_role,
        action_type=action_type,
        from_status=from_status,
        to_status=to_status,
        comment=comment,
        digital_acknowledgement=acknowledgement,
        ip_address=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def _audit_trail_rows(report):
    rows = []
    status_labels = dict(TNYReport.STATUS_CHOICES)
    for action in report.approval_actions.select_related("user"):
        rows.append([
            ("iTavi e Qaravi", action.get_action_type_display()),
            ("Vakailesilesi", action.user_full_name),
            ("iTutu", action.user_role),
            ("iTuvaki e Liu", status_labels.get(action.from_status, action.from_status or "-")),
            ("iTuvaki Vou", status_labels.get(action.to_status, action.to_status or "-")),
            ("Vakamacala", action.comment or "-"),
            ("Vakadinadina Vakadigital", action.digital_acknowledgement),
            ("Siga kei na Gauna", timezone.localtime(action.created_at).strftime("%d %b %Y %H:%M")),
        ])
    return rows


def _handle_report_form(request, report, profile, *, initial_seeds=False):
    if request.method == "POST":
        post_data = _with_missing_defaults(request.POST, report)
        form = TNYReportForm(post_data, instance=report)
        formsets = _get_tny_formsets(data=post_data, instance=report)
        present_formsets = _bound_formsets(formsets)
        if form.is_valid() and all(formset.is_valid() for formset in present_formsets):
            action = request.POST.get("action", "save_draft")
            with transaction.atomic():
                report = form.save(commit=False)
                original_status = report.status
                if action == "submit_report":
                    report.submit()
                elif report.status != TNYReport.STATUS_RETURNED_BY_ROKO:
                    report.status = TNYReport.STATUS_DRAFT
                    report.submitted_at = None
                report.save()
                for formset in present_formsets:
                    formset.instance = report
                    formset.save()
                if action == "submit_report":
                    record_approval_action(
                        request,
                        report,
                        TNYApprovalAction.ACTION_SUBMIT,
                        comment="Report submitted for Roko Tui approval.",
                        to_status=report.status,
                        from_status=original_status,
                    )
            if action == "submit_report":
                messages.success(request, "Sa vakau na iVolavola ni Turaga ni Yavusa.")
                return redirect("turaga_ni_yavusa:report_detail", pk=report.pk)
            messages.success(request, "Sa maroroi na draft.")
            return redirect("turaga_ni_yavusa:report_edit", pk=report.pk)
    else:
        form = TNYReportForm(instance=report)
        formsets = _get_tny_formsets(instance=report if report.pk else None, initial_seeds=initial_seeds)
    return render(request, "turaga_ni_yavusa/report_form.html", {"form": form, "form_blocks": _report_form_blocks(form, formsets), "profile": profile, "report": report if report.pk else None})


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
def report_list(request):
    return render(request, "turaga_ni_yavusa/report_list.html", {"reports": reports_for(request.user).order_by("-year", "-created_at")})


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
def report_create(request):
    owner_profile, response = resolve_report_owner(request, TuragaProfile.TURAGA_NI_YAVUSA, "turaga_ni_yavusa:report_create")
    if response:
        return response
    profile, defaults = _profile_report_defaults(owner_profile.user)
    return _handle_report_form(request, TNYReport(**defaults), profile, initial_seeds=True)


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
def report_edit(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not can_edit_report(request.user, report):
        messages.error(request, "Sa tiko na ripote qo ena kena dikevi ka sega ni rawa ni veisautaki.")
        return redirect("turaga_ni_yavusa:report_detail", pk=report.pk)
    profile, _ = _profile_report_defaults(report.owner or request.user)
    return _handle_report_form(request, report, profile)


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
def report_detail(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    return render(request, "turaga_ni_yavusa/report_detail.html", {
        "report": report,
        "stats": [("E Tiko", report.residents_total), ("E Lako", report.away_total), ("Itutu", report.confirmed_titles_this_period), ("Kawa Bula", report.genealogy_recorded_count)],
        "sections": _detail_sections(report),
        "child_sections": [("Vakadinadina", _model_rows(report.signatures.all()))],
        "approval_actions": report.approval_actions.select_related("user"),
        "workflow_actions": workflow_actions_for(request.user, report),
        "approval_form": ApprovalActionForm(),
        "can_edit_report": can_edit_report(request.user, report),
        "can_export_report": can_export_report(report),
    })


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
@require_POST
def report_workflow_action(request, pk, action_type):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not is_roko_user(request.user):
        raise PermissionDenied
    form = ApprovalActionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please confirm the digital acknowledgement before continuing.")
        return redirect("turaga_ni_yavusa:report_detail", pk=report.pk)
    try:
        record_approval_action(
            request,
            report,
            action_type,
            comment=form.cleaned_data.get("comment", ""),
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if exc.messages else "Invalid workflow action.")
        return redirect("turaga_ni_yavusa:report_detail", pk=report.pk)
    messages.success(request, "The Roko Tui approval action was recorded.")
    return redirect("turaga_ni_yavusa:report_detail", pk=report.pk)


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
def report_pdf(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not can_export_report(report):
        messages.error(request, "E dodonu me vakadonui mada na ripote qo mai vua na Roko Tui ni bera ni export taki.")
        return redirect("turaga_ni_yavusa:report_detail", pk=report.pk)
    return report_pdf_response(
        title="Turaga ni Yavusa Quarterly Report",
        subtitle=f"{report.yavusa} - {report.vanua} - {report.quarter} {report.year}",
        meta_rows=[
            ("iTutu", "Turaga ni Yavusa"),
            ("Yacamuni", report.full_name),
            ("Yavusa", report.yavusa),
            ("Vanua", report.vanua),
            ("Ripote ni vula ko", report.quarter),
            ("Ena yabaki ko", report.year),
            ("iTuvaki", report.get_status_display()),
            ("Siga ni vakau", report.submitted_at.strftime("%d %b %Y") if report.submitted_at else "-"),
        ],
        sections=_detail_sections(report),
        child_sections=[("Vakadinadina", _model_rows(report.signatures.all()))],
        audit_rows=_audit_trail_rows(report),
        filename=f"turaga-ni-yavusa-{report.yavusa}-{report.quarter}-{report.year}.pdf".replace(" ", "-").lower(),
    )


def _reference_data(reports, profile=None):
    reference_reports = _koro_reference_reports(reports, profile).prefetch_related("population", "housing_counts", "businesses")
    return {
        "report_count": reference_reports.count(),
        "population_total": PopulationAgeGroup.objects.filter(report__in=reference_reports).aggregate(total=Sum("count"))["total"] or 0,
        "household_total": reference_reports.aggregate(total=Sum("household_count"))["total"] or 0,
        "business_total": Business.objects.filter(report__in=reference_reports).count(),
        "housing_total": HousingCount.objects.filter(report__in=reference_reports).aggregate(total=Sum("count"))["total"] or 0,
    }


def _koro_reference_reports(reports, profile=None):
    villages = set(reports.exclude(koro="").values_list("koro", flat=True).distinct())
    tikina = set(reports.exclude(tikina="").values_list("tikina", flat=True).distinct())

    if profile:
        if getattr(profile, "village", ""):
            villages.add(profile.village)
        if getattr(profile, "district", ""):
            tikina.add(profile.district)

    qs = TNKReport.objects.none()
    if villages:
        qs = TNKReport.objects.filter(village__in=villages)
    if tikina:
        tikina_qs = TNKReport.objects.filter(district__in=tikina)
        qs = qs | tikina_qs if villages else tikina_qs

    return qs.distinct().order_by("-year", "-created_at")


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
def turaga_ni_yavusa_dashboard(request):
    reports = reports_for(request.user).order_by("-year", "-created_at")
    profile = getattr(request.user, "turaga_profile", None)
    koro_reports = _koro_reference_reports(reports, profile)
    tnk_review_queue = koro_reports.filter(status=TNKReport.STATUS_SUBMITTED_TO_LIULIU)
    return render(request, "turaga_ni_yavusa/dashboard.html", {
        "profile": profile,
        "reports": reports[:5],
        "analysis": tny_dashboard_analysis(reports),
        "reference_data": _reference_data(reports, profile),
        "koro_analysis": tnk_dashboard_analysis(koro_reports),
        "tnk_review_queue": tnk_review_queue,
    })
