from collections import OrderedDict

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import is_roko_user, membership_required
from accounts.models import TuragaProfile
from turani.models import Business, HousingCount, PopulationAgeGroup, TNKReport

from .analytics import tny_dashboard_analysis
from .forms import SignatureFormSet, TNY_FORMSET_TITLES, TNY_SECTIONS, TNYReportForm
from .models import Signature, TNYReport


REPORT_PREFETCHES = ("signatures",)


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
        "tokatoka": profile.tokatoka,
        "mataqali": profile.mataqali,
        "yavusa": profile.yavusa,
        "vanua": profile.vanua,
        "koro": profile.village,
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


def _field_value(obj, field):
    value = getattr(obj, field.name)
    if field.choices:
        value = getattr(obj, f"get_{field.name}_display")()
    elif isinstance(value, bool):
        value = "Io" if value else "Sega"
    elif value in (None, ""):
        value = "-"
    return field.verbose_name.title(), value


def _detail_sections(report):
    return [
        (title, [_field_value(report, report._meta.get_field(name)) for name in names])
        for title, names in TNY_SECTIONS
    ]


def _model_rows(items):
    rows = []
    for item in items:
        rows.append([_field_value(item, field) for field in item._meta.fields if field.name not in {"id", "report"}])
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
                if action == "submit_report":
                    report.submit()
                elif report.status != TNYReport.STATUS_SUBMITTED:
                    report.status = TNYReport.STATUS_DRAFT
                    report.submitted_at = None
                report.save()
                for formset in present_formsets:
                    formset.instance = report
                    formset.save()
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


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA)
def report_create(request):
    profile, defaults = _profile_report_defaults(request.user)
    return _handle_report_form(request, TNYReport(**defaults), profile, initial_seeds=True)


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA)
def report_edit(request, pk):
    profile, _ = _profile_report_defaults(request.user)
    report = get_object_or_404(reports_for(request.user), pk=pk)
    return _handle_report_form(request, report, profile)


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
def report_detail(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    return render(request, "turaga_ni_yavusa/report_detail.html", {
        "report": report,
        "stats": [("E Tiko", report.residents_total), ("E Lako", report.away_total), ("Itutu", report.confirmed_titles_this_period), ("Kawa Bula", report.genealogy_recorded_count)],
        "sections": _detail_sections(report),
        "child_sections": [("Vakadinadina", _model_rows(report.signatures.all()))],
    })


def _reference_data(reports):
    villages = list(reports.exclude(koro="").values_list("koro", flat=True).distinct())
    reference_reports = TNKReport.objects.filter(village__in=villages).prefetch_related("population", "housing_counts", "businesses")
    return {
        "report_count": reference_reports.count(),
        "population_total": PopulationAgeGroup.objects.filter(report__in=reference_reports).aggregate(total=Sum("count"))["total"] or 0,
        "household_total": reference_reports.aggregate(total=Sum("household_count"))["total"] or 0,
        "business_total": Business.objects.filter(report__in=reference_reports).count(),
        "housing_total": HousingCount.objects.filter(report__in=reference_reports).aggregate(total=Sum("count"))["total"] or 0,
    }


@membership_required(TuragaProfile.TURAGA_NI_YAVUSA, allow_roko=True)
def turaga_ni_yavusa_dashboard(request):
    reports = reports_for(request.user).order_by("-year", "-created_at")
    return render(request, "turaga_ni_yavusa/dashboard.html", {"reports": reports[:5], "analysis": tny_dashboard_analysis(reports), "reference_data": _reference_data(reports)})
