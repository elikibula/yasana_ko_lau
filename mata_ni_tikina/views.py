from collections import OrderedDict

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import is_roko_user, membership_required
from accounts.models import TuragaProfile
from turani.models import Business, HousingCount, PopulationAgeGroup, TNKReport

from .analytics import mnt_dashboard_analysis
from .forms import (
    ChallengeIndicatorFormSet,
    CoordinationStatusFormSet,
    DisputeFormSet,
    FundChallengeFormSet,
    IncomeActivityFormSet,
    IncomeSourceFormSet,
    KoroUnderTikinaFormSet,
    MNT_FORMSET_TITLES,
    MNT_SECTIONS,
    MNTReportForm,
    SavingsAccountFormSet,
    SettlementRegistrationFormSet,
    SignatureFormSet,
    SocialIndicatorFormSet,
    TreePlantingFormSet,
    VagalalaSettlementFormSet,
    VillageVisitFormSet,
)
from .models import (
    FundCollectionChallenge,
    MNTReport,
    Signature,
    TikinaChallengeIndicator,
    TikinaCoordinationStatus,
    TikinaIncomeActivity,
    TikinaSocialIndicator,
)


REPORT_PREFETCHES = (
    "koro_under_tikina",
    "vagalala_settlements",
    "settlement_registrations",
    "coordination_statuses",
    "disputes",
    "social_indicators",
    "income_sources",
    "tree_planting_trainings",
    "income_activities",
    "savings_accounts",
    "fund_challenges",
    "challenge_indicators",
    "village_visits",
    "signatures",
)


FORMSET_SPECS = (
    ("koro_under_tikina", "koro", KoroUnderTikinaFormSet),
    ("vagalala_settlements", "vagalala", VagalalaSettlementFormSet),
    ("settlement_registrations", "setreg", SettlementRegistrationFormSet),
    ("coordination_status", "coord", CoordinationStatusFormSet),
    ("disputes", "disputes", DisputeFormSet),
    ("social_indicators", "social", SocialIndicatorFormSet),
    ("income_sources", "income", IncomeSourceFormSet),
    ("tree_planting", "tree", TreePlantingFormSet),
    ("income_activities", "activities", IncomeActivityFormSet),
    ("savings_accounts", "savings", SavingsAccountFormSet),
    ("fund_challenges", "fundch", FundChallengeFormSet),
    ("challenge_indicators", "chall", ChallengeIndicatorFormSet),
    ("village_visits", "visits", VillageVisitFormSet),
    ("signatures", "signatures", SignatureFormSet),
)


def reports_for(user):
    qs = MNTReport.objects.select_related("owner").prefetch_related(*REPORT_PREFETCHES)
    return qs if is_roko_user(user) else qs.filter(owner=user)


def _get_mnt_formsets(data=None, instance=None, initial_seeds=False):
    def kwargs_for(prefix):
        kwargs = {"instance": instance}
        if data is not None and f"{prefix}-TOTAL_FORMS" in data:
            kwargs["data"] = data
        return kwargs

    formsets = OrderedDict((key, formset(**kwargs_for(prefix), prefix=prefix)) for key, prefix, formset in FORMSET_SPECS)
    if initial_seeds and instance is None and data is None:
        formsets["coordination_status"] = CoordinationStatusFormSet(prefix="coord", initial=[{"entity": value} for value, _ in TikinaCoordinationStatus.ENTITY_CHOICES])
        formsets["social_indicators"] = SocialIndicatorFormSet(prefix="social", initial=[{"indicator": value} for value, _ in TikinaSocialIndicator.INDICATOR_CHOICES])
        formsets["income_activities"] = IncomeActivityFormSet(prefix="activities", initial=[{"activity": value} for value, _ in TikinaIncomeActivity.ACTIVITY_CHOICES])
        formsets["fund_challenges"] = FundChallengeFormSet(prefix="fundch", initial=[{"challenge": value} for value, _ in FundCollectionChallenge.CHALLENGE_CHOICES])
        formsets["challenge_indicators"] = ChallengeIndicatorFormSet(prefix="chall", initial=[{"indicator": value} for value, _ in TikinaChallengeIndicator.INDICATOR_CHOICES])
        formsets["signatures"] = SignatureFormSet(prefix="signatures", initial=[{"role": value} for value, _ in Signature.ROLE_CHOICES])
    return formsets


def _profile_report_defaults(user):
    profile, _ = TuragaProfile.objects.get_or_create(user=user)
    return profile, {
        "owner": user,
        "full_name": profile.full_name,
        "age": profile.age,
        "village": profile.village,
        "tikina": profile.district or profile.vanua,
        "province": profile.province,
        "council_head_name": profile.full_name,
        "council_head_age": profile.age,
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


def _matrix_rows(formset):
    return [(form.initial.get("entity") or form.initial.get("indicator") or form.initial.get("activity") or form.initial.get("challenge") or form.instance.pk, [form]) for form in formset.forms]


def _report_form_blocks(form, formsets):
    blocks = [
        {"type": "chapter", "title": "TUKUTUKU RARABA"},
        {"type": "section", "title": "1.1-1.6 Tukutuku Raraba", "fields": _form_fields(form, ("quarter", "year", "full_name", "age", "village", "tikina", "province", "tikina_population"))},
        {"type": "formset", "key": "koro_under_tikina", "title": MNT_FORMSET_TITLES["koro_under_tikina"], "formset": formsets["koro_under_tikina"]},
        {"type": "formset", "key": "vagalala_settlements", "title": MNT_FORMSET_TITLES["vagalala_settlements"], "formset": formsets["vagalala_settlements"]},
        {"type": "section", "title": "1.8 Ai Cavuti Raraba Vakavanua", "fields": _form_fields(form, ("announcements_made_count", "traditional_announcements_received_count"))},
        {"type": "section", "title": "1.10 iTuvaki ni Sovei ni Koro", "fields": _form_fields(form, ("villages_surveyed_count", "villages_pending_survey_count"))},
        {"type": "formset", "key": "settlement_registrations", "title": MNT_FORMSET_TITLES["settlement_registrations"], "formset": formsets["settlement_registrations"]},
        {"type": "chapter", "title": "MATABOSE NI TIKINA"},
        {"type": "section", "title": "2.0 Matabose ni Tikina", "fields": _form_fields(form, ("council_head_name", "council_head_age", "council_turaga_count", "council_marama_count", "council_daunivakasala_count", "council_meeting_frequency", "council_additional_notes"))},
        {"type": "chapter", "title": "SEMA KEI NA CAKACAKAVATA"},
        {"type": "matrix", "key": "coordination_status", "title": MNT_FORMSET_TITLES["coordination_status"], "formset": formsets["coordination_status"], "rows": _matrix_rows(formsets["coordination_status"]), "column_labels": ["iTuvaki"]},
        {"type": "formset", "key": "disputes", "title": MNT_FORMSET_TITLES["disputes"], "formset": formsets["disputes"]},
        {"type": "section", "title": "iKuri ni Vakamacala", "fields": _form_fields(form, ("coordination_additional_notes",))},
        {"type": "chapter", "title": "TUVATUVA NI MATABOSE NI TIKINA"},
        {"type": "section", "title": "4.1 Development Plan", "fields": _form_fields(form, ("has_development_plan",))},
        {"type": "matrix", "key": "social_indicators", "title": MNT_FORMSET_TITLES["social_indicators"], "formset": formsets["social_indicators"], "rows": _matrix_rows(formsets["social_indicators"]), "column_labels": ["Trend"]},
        {"type": "section", "title": "Education Decision", "fields": _form_fields(form, ("education_council_decision",))},
        {"type": "formset", "key": "income_sources", "title": MNT_FORMSET_TITLES["income_sources"], "formset": formsets["income_sources"]},
        {"type": "formset", "key": "tree_planting", "title": MNT_FORMSET_TITLES["tree_planting"], "formset": formsets["tree_planting"]},
        {"type": "matrix", "key": "income_activities", "title": MNT_FORMSET_TITLES["income_activities"], "formset": formsets["income_activities"], "rows": _matrix_rows(formsets["income_activities"]), "column_labels": ["Toqa"]},
        {"type": "section", "title": "Income and Infrastructure", "fields": _form_fields(form, ("income_trend", "income_council_decision", "infrastructure_trend", "villages_with_phone_count", "villages_with_tv_count", "boat_count", "vehicle_count", "villages_with_road_access_count", "new_roads_built_km", "development_council_decision"))},
        {"type": "section", "title": "Government Partnership", "fields": _form_fields(form, ("govt_financial_assistance_amount", "govt_assisting_department", "govt_official_visits_count", "govt_projects_covered", "govt_partnership_notes"))},
        {"type": "section", "title": "NGO Partnership", "fields": _form_fields(form, ("ngo_awareness_programs_notes", "ngo_financial_assistance_amount", "ngo_program_name", "ngo_project_equipment_value", "ngo_project_name", "ngo_partnership_notes"))},
        {"type": "chapter", "title": "NA VEIKA VAKAILAVO"},
        {"type": "section", "title": "Soli and Funds", "fields": _form_fields(form, ("council_funds_held", "soli_target_amount", "soli_contributor_count", "soli_collected_amount", "soli_balance_amount", "soli_collection_method", "fund_growth_notes"))},
        {"type": "formset", "key": "savings_accounts", "title": MNT_FORMSET_TITLES["savings_accounts"], "formset": formsets["savings_accounts"]},
        {"type": "matrix", "key": "fund_challenges", "title": MNT_FORMSET_TITLES["fund_challenges"], "formset": formsets["fund_challenges"], "rows": _matrix_rows(formsets["fund_challenges"]), "column_labels": ["Toqa"]},
        {"type": "chapter", "title": "TUVAKI NI QELE NI TEITEI"},
        {"type": "section", "title": "Farmland", "fields": _form_fields(form, ("has_registered_farmland", "farmland_lease_count", "farmland_acres_leased", "farmland_lease_years_covered", "farmland_development_notes"))},
        {"type": "chapter", "title": "VAKAITAVI NI VAKAILESILESI"},
        {"type": "section", "title": "Representative Participation", "fields": _form_fields(form, ("reps_attend_meetings", "reps_understand_training_needs", "reps_assist_report_writing", "reps_help_outside_meetings", "reps_additional_notes", "reps_council_decision"))},
        {"type": "matrix", "key": "challenge_indicators", "title": MNT_FORMSET_TITLES["challenge_indicators"], "formset": formsets["challenge_indicators"], "rows": _matrix_rows(formsets["challenge_indicators"]), "column_labels": ["Toqa"]},
        {"type": "chapter", "title": "VEITALEVI ENA VEIKORO"},
        {"type": "formset", "key": "village_visits", "title": MNT_FORMSET_TITLES["village_visits"], "formset": formsets["village_visits"]},
        {"type": "chapter", "title": "VAKADINADINA"},
        {"type": "formset", "key": "signatures", "title": MNT_FORMSET_TITLES["signatures"], "formset": formsets["signatures"]},
    ]
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
    return [(title, [_field_value(report, report._meta.get_field(name)) for name in names]) for title, names in MNT_SECTIONS]


def _model_rows(items):
    return [[_field_value(item, field) for field in item._meta.fields if field.name not in {"id", "report"}] for item in items]


def _child_sections(report):
    return [(MNT_FORMSET_TITLES[key], _model_rows(getattr(report, related).all())) for key, related in (
        ("koro_under_tikina", "koro_under_tikina"),
        ("vagalala_settlements", "vagalala_settlements"),
        ("settlement_registrations", "settlement_registrations"),
        ("coordination_status", "coordination_statuses"),
        ("disputes", "disputes"),
        ("social_indicators", "social_indicators"),
        ("income_sources", "income_sources"),
        ("tree_planting", "tree_planting_trainings"),
        ("income_activities", "income_activities"),
        ("savings_accounts", "savings_accounts"),
        ("fund_challenges", "fund_challenges"),
        ("challenge_indicators", "challenge_indicators"),
        ("village_visits", "village_visits"),
        ("signatures", "signatures"),
    )]


def _handle_report_form(request, report, profile, *, initial_seeds=False):
    if request.method == "POST":
        post_data = _with_missing_defaults(request.POST, report)
        form = MNTReportForm(post_data, instance=report)
        formsets = _get_mnt_formsets(data=post_data, instance=report)
        present_formsets = _bound_formsets(formsets)
        if form.is_valid() and all(formset.is_valid() for formset in present_formsets):
            action = request.POST.get("action", "save_draft")
            with transaction.atomic():
                report = form.save(commit=False)
                if action == "submit_report":
                    report.submit()
                elif report.status != MNTReport.STATUS_SUBMITTED:
                    report.status = MNTReport.STATUS_DRAFT
                    report.submitted_at = None
                report.save()
                for formset in present_formsets:
                    formset.instance = report
                    formset.save()
            if action == "submit_report":
                messages.success(request, "Sa vakau na iVolavola ni Mata ni Tikina.")
                return redirect("mata_ni_tikina:report_detail", pk=report.pk)
            messages.success(request, "Sa maroroi na draft.")
            return redirect("mata_ni_tikina:report_edit", pk=report.pk)
    else:
        form = MNTReportForm(instance=report)
        formsets = _get_mnt_formsets(instance=report if report.pk else None, initial_seeds=initial_seeds)
    return render(request, "mata_ni_tikina/report_form.html", {"form": form, "form_blocks": _report_form_blocks(form, formsets), "profile": profile, "report": report if report.pk else None})


@membership_required(TuragaProfile.MATA_NI_TIKINA, allow_roko=True)
def report_list(request):
    return render(request, "mata_ni_tikina/report_list.html", {"reports": reports_for(request.user).order_by("-year", "-created_at")})


@membership_required(TuragaProfile.MATA_NI_TIKINA)
def report_create(request):
    profile, defaults = _profile_report_defaults(request.user)
    return _handle_report_form(request, MNTReport(**defaults), profile, initial_seeds=True)


@membership_required(TuragaProfile.MATA_NI_TIKINA)
def report_edit(request, pk):
    profile, _ = _profile_report_defaults(request.user)
    return _handle_report_form(request, get_object_or_404(reports_for(request.user), pk=pk), profile)


@membership_required(TuragaProfile.MATA_NI_TIKINA, allow_roko=True)
def report_detail(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    return render(request, "mata_ni_tikina/report_detail.html", {"report": report, "stats": [("Koro", report.total_villages_under_buli()), ("Veileti", report.total_disputes()), ("Soli", report.soli_collected_amount or 0), ("Visits", report.village_visits.count())], "sections": _detail_sections(report), "child_sections": _child_sections(report)})


def _reference_data(reports):
    tikina_names = list(reports.exclude(tikina="").values_list("tikina", flat=True).distinct())
    reference_reports = TNKReport.objects.filter(district__in=tikina_names).prefetch_related("population", "housing_counts", "businesses")
    return {
        "report_count": reference_reports.count(),
        "population_total": PopulationAgeGroup.objects.filter(report__in=reference_reports).aggregate(total=Sum("count"))["total"] or 0,
        "household_total": reference_reports.aggregate(total=Sum("household_count"))["total"] or 0,
        "business_total": Business.objects.filter(report__in=reference_reports).count(),
        "housing_total": HousingCount.objects.filter(report__in=reference_reports).aggregate(total=Sum("count"))["total"] or 0,
    }


@membership_required(TuragaProfile.MATA_NI_TIKINA, allow_roko=True)
def mata_ni_tikina_dashboard(request):
    reports = reports_for(request.user).order_by("-year", "-created_at")
    return render(request, "mata_ni_tikina/dashboard.html", {"reports": reports[:5], "analysis": mnt_dashboard_analysis(reports), "reference_data": _reference_data(reports)})
