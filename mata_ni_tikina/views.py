from collections import OrderedDict

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import is_roko_user, membership_required
from accounts.models import TuragaProfile
from accounts.reporting import resolve_report_owner
from common.pdf_exports import report_pdf_response
from koro.models import Koro
from tikina.models import Tikina
from turani.forms import ApprovalActionForm
from turani.models import Business, HousingCount, PopulationAgeGroup, TNKReport

from .analytics import mnt_dashboard_analysis
from .forms import (
    ChallengeIndicatorFormSet,
    CoordinationStatusFormSet,
    DisputeFormSet,
    EducationTrainingFormSet,
    FundChallengeFormSet,
    IncomeActivityFormSet,
    IncomeSourceFormSet,
    KoroUnderTikinaFormSet,
    MNT_FIJIAN_INLINE_LABELS,
    MNT_FORMSET_TITLES,
    MNT_SECTIONS,
    MNTReportForm,
    SavingsAccountFormSet,
    SettlementRegistrationFormSet,
    SocialIndicatorFormSet,
    TreePlantingFormSet,
    VagalalaSettlementFormSet,
    VillageVisitFormSet,
)
from .models import (
    FundCollectionChallenge,
    MNTApprovalAction,
    MNTReport,
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
    "education_trainings",
    "income_sources",
    "tree_planting_trainings",
    "income_activities",
    "savings_accounts",
    "fund_challenges",
    "challenge_indicators",
    "village_visits",
)


DETAIL_FORMSETS = (
    KoroUnderTikinaFormSet,
    VagalalaSettlementFormSet,
    SettlementRegistrationFormSet,
    CoordinationStatusFormSet,
    DisputeFormSet,
    SocialIndicatorFormSet,
    EducationTrainingFormSet,
    IncomeSourceFormSet,
    TreePlantingFormSet,
    IncomeActivityFormSet,
    SavingsAccountFormSet,
    FundChallengeFormSet,
    ChallengeIndicatorFormSet,
    VillageVisitFormSet,
)


DETAIL_LABELS_BY_MODEL = {
    formset.model.__name__: {
        **MNT_FIJIAN_INLINE_LABELS.get(formset.model.__name__, {}),
        **(getattr(formset.form._meta, "labels", None) or {}),
    }
    for formset in DETAIL_FORMSETS
}


ACTION_LABELS = {
    MNTApprovalAction.ACTION_APPROVE: "Vakadonuya",
    MNTApprovalAction.ACTION_RETURN: "Vakalesuya me Vakadodonutaki",
    MNTApprovalAction.ACTION_REJECT: "Cata",
    MNTApprovalAction.ACTION_COMMENT: "Vakamacala",
}


FORMSET_SPECS = (
    ("koro_under_tikina", "koro", KoroUnderTikinaFormSet),
    ("vagalala_settlements", "vagalala", VagalalaSettlementFormSet),
    ("settlement_registrations", "setreg", SettlementRegistrationFormSet),
    ("coordination_status", "coord", CoordinationStatusFormSet),
    ("disputes", "disputes", DisputeFormSet),
    ("social_indicators", "social", SocialIndicatorFormSet),
    ("education_trainings", "edutrain", EducationTrainingFormSet),
    ("income_sources", "income", IncomeSourceFormSet),
    ("tree_planting", "tree", TreePlantingFormSet),
    ("income_activities", "activities", IncomeActivityFormSet),
    ("savings_accounts", "savings", SavingsAccountFormSet),
    ("fund_challenges", "fundch", FundChallengeFormSet),
    ("challenge_indicators", "chall", ChallengeIndicatorFormSet),
    ("village_visits", "visits", VillageVisitFormSet),
)


def reports_for(user):
    qs = MNTReport.objects.select_related("owner").prefetch_related(*REPORT_PREFETCHES)
    return qs if is_roko_user(user) else qs.filter(owner=user)


def _koro_initial_for_tikina(tikina_name):
    if not tikina_name:
        return []
    tikina = Tikina.objects.filter(name__iexact=tikina_name).first()
    if not tikina:
        return []
    rows = []
    for koro in Koro.objects.filter(tikina=tikina).select_related("turaga_ni_koro__user").order_by("-is_koro_turaga", "name"):
        leader = ""
        if koro.turaga_ni_koro_id:
            leader = koro.turaga_ni_koro.user.get_full_name().strip() or koro.turaga_ni_koro.user.get_username()
        rows.append({"village_name": koro.name, "traditional_leader": leader})
    return rows


def _koro_names_for_tikina(tikina_name):
    if not tikina_name:
        return []
    tikina = Tikina.objects.filter(name__iexact=tikina_name).first()
    if not tikina:
        return []
    return list(Koro.objects.filter(tikina=tikina).values_list("name", flat=True))


def _calculate_tikina_population(tikina_name, quarter=None, year=None):
    if not tikina_name:
        return 0
    report_filter = Q(district__iexact=tikina_name)
    for koro_name in _koro_names_for_tikina(tikina_name):
        report_filter |= Q(village__iexact=koro_name)
    reports = TNKReport.objects.filter(report_filter, status=TNKReport.STATUS_SUBMITTED)
    if quarter:
        reports = reports.filter(quarter=quarter)
    if year:
        reports = reports.filter(year=year)
    return PopulationAgeGroup.objects.filter(report__in=reports).aggregate(total=Sum("count"))["total"] or 0


def _refresh_report_auto_totals(report):
    report.tikina_population = _calculate_tikina_population(report.tikina, report.quarter, report.year)
    report.council_total_attendees = (
        (report.council_turaga_count or 0)
        + (report.council_marama_count or 0)
        + (report.council_daunivakasala_count or 0)
    )
    if report.pk:
        totals = report.vagalala_settlements.aggregate(population=Sum("population_count"), families=Sum("family_count"))
        report.vagalala_population_total = totals["population"] or 0
        report.vagalala_family_total = totals["families"] or 0


def _ensure_koro_rows_for_tikina(report):
    if not report.pk:
        return
    existing_names = {name.casefold() for name in report.koro_under_tikina.values_list("village_name", flat=True)}
    missing_rows = []
    for row in _koro_initial_for_tikina(report.tikina):
        if row["village_name"].casefold() in existing_names:
            continue
        missing_rows.append(report.koro_under_tikina.model(report=report, **row))
    if missing_rows:
        report.koro_under_tikina.model.objects.bulk_create(missing_rows)


def _get_mnt_formsets(data=None, instance=None, initial_seeds=False, tikina_name=""):
    def kwargs_for(prefix):
        kwargs = {"instance": instance}
        if data is not None and f"{prefix}-TOTAL_FORMS" in data:
            kwargs["data"] = data
        return kwargs

    formsets = OrderedDict((key, formset(**kwargs_for(prefix), prefix=prefix)) for key, prefix, formset in FORMSET_SPECS)
    if initial_seeds and instance is None and data is None:
        koro_initial = _koro_initial_for_tikina(tikina_name)
        if koro_initial:
            koro_formset = KoroUnderTikinaFormSet(prefix="koro", initial=koro_initial)
            koro_formset.extra = len(koro_initial) + 1
            formsets["koro_under_tikina"] = koro_formset
        formsets["coordination_status"] = CoordinationStatusFormSet(prefix="coord", initial=[{"entity": value} for value, _ in TikinaCoordinationStatus.ENTITY_CHOICES])
        formsets["social_indicators"] = SocialIndicatorFormSet(prefix="social", initial=[{"indicator": value} for value, _ in TikinaSocialIndicator.INDICATOR_CHOICES])
        formsets["income_activities"] = IncomeActivityFormSet(prefix="activities", initial=[{"activity": value} for value, _ in TikinaIncomeActivity.ACTIVITY_CHOICES])
        formsets["fund_challenges"] = FundChallengeFormSet(prefix="fundch", initial=[{"challenge": value} for value, _ in FundCollectionChallenge.CHALLENGE_CHOICES])
        formsets["challenge_indicators"] = ChallengeIndicatorFormSet(prefix="chall", initial=[{"indicator": value} for value, _ in TikinaChallengeIndicator.INDICATOR_CHOICES])
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
        {"type": "section", "title": "1.8 Ai Cavuti Raraba Vakavanua ni Jikina", "fields": _form_fields(form, ("announcements_made_count", "traditional_announcements_received_count"))},
        {"type": "formset", "key": "vagalala_settlements", "title": MNT_FORMSET_TITLES["vagalala_settlements"], "formset": formsets["vagalala_settlements"]},
        {"type": "section", "title": "1.9 Wiliwili Taucoko ni iTikotiko Vagalala", "fields": _form_fields(form, ("vagalala_population_total", "vagalala_family_total"))},
        {"type": "section", "title": "1.10 Soveyataki ni Koro", "fields": _form_fields(form, ("villages_surveyed_count", "villages_pending_survey_count"))},
        {"type": "formset", "key": "settlement_registrations", "title": MNT_FORMSET_TITLES["settlement_registrations"], "formset": formsets["settlement_registrations"]},
        {"type": "chapter", "title": "MATABOSE NI TIKINA"},
        {"type": "section", "title": "2.0 Matabose ni Tikina", "fields": _form_fields(form, ("council_head_name", "council_head_age", "council_turaga_count", "council_marama_count", "council_daunivakasala_count", "council_total_attendees", "council_meeting_frequency", "council_additional_notes"))},
        {"type": "chapter", "title": "SEMA KEI NA CAKACAKAVATA"},
        {"type": "matrix", "key": "coordination_status", "title": MNT_FORMSET_TITLES["coordination_status"], "formset": formsets["coordination_status"], "rows": _matrix_rows(formsets["coordination_status"]), "column_labels": ["iTuvaki"]},
        {"type": "section", "title": "iKuri ni Vakamacala", "fields": _form_fields(form, ("coordination_additional_notes",))},
        {"type": "formset", "key": "disputes", "title": MNT_FORMSET_TITLES["disputes"], "formset": formsets["disputes"]},
        {"type": "chapter", "title": "TUVATUVA NI MATABOSE NI TIKINA"},
        {"type": "section", "title": "4.1 Development Plan", "fields": _form_fields(form, ("has_development_plan",))},
        {"type": "matrix", "key": "social_indicators", "title": MNT_FORMSET_TITLES["social_indicators"], "formset": formsets["social_indicators"], "rows": _matrix_rows(formsets["social_indicators"]), "column_labels": ["Trend"]},
        {"type": "formset", "key": "education_trainings", "title": MNT_FORMSET_TITLES["education_trainings"], "formset": formsets["education_trainings"]},
        {"type": "section", "title": "4.2 Lewa ni Matabose me baleta na Vuli", "fields": _form_fields(form, ("education_council_decision", "education_next_quarter_decision"))},
        {"type": "formset", "key": "income_sources", "title": MNT_FORMSET_TITLES["income_sources"], "formset": formsets["income_sources"]},
        {"type": "formset", "key": "tree_planting", "title": MNT_FORMSET_TITLES["tree_planting"], "formset": formsets["tree_planting"]},
        {"type": "section", "title": "4.5 Vurevure ni Lavo kei na Veivakatorocaketaki", "fields": _form_fields(form, ("income_trend", "income_council_decision", "infrastructure_trend", "villages_with_phone_count", "villages_with_tv_count", "boat_count", "vehicle_count", "villages_with_road_access_count", "new_roads_built_km", "development_council_decision"))},
        {"type": "section", "title": "4.6 Cakacakavata kei na Matanitu", "fields": _form_fields(form, ("govt_financial_assistance_amount", "govt_assisting_department", "govt_official_visits_count", "govt_projects_covered", "govt_partnership_notes"))},
        {"type": "section", "title": "4.7 Vakacakavata kei na veitabana tale eso se NGO's", "fields": _form_fields(form, ("ngo_awareness_programs_notes", "ngo_financial_assistance_amount", "ngo_program_name", "ngo_project_equipment_value", "ngo_project_name", "ngo_partnership_notes"))},
        {"type": "chapter", "title": "5.0 NA VEIKA VAKAI LAVO"},
        {"type": "matrix", "key": "income_activities", "title": MNT_FORMSET_TITLES["income_activities"], "formset": formsets["income_activities"], "rows": _matrix_rows(formsets["income_activities"]), "column_labels": ["Toqa"]},
        {"type": "section", "title": "5.2 Lavo ni Matabose ni Jikina", "fields": [], "formsets": [{"key": "savings_accounts", "formset": formsets["savings_accounts"]}]},
        {"type": "section", "title": "5.3 Soli ni Yasana", "fields": _form_fields(form, ("soli_target_amount", "soli_contributor_count", "soli_collected_amount", "soli_balance_amount", "soli_collection_method"))},
        {"type": "matrix", "key": "fund_challenges", "title": MNT_FORMSET_TITLES["fund_challenges"], "formset": formsets["fund_challenges"], "rows": _matrix_rows(formsets["fund_challenges"]), "column_labels": ["Toqa"]},
        {"type": "section", "title": "5.6 Vakamacala ni Tubucake ni Lavo", "fields": _form_fields(form, ("fund_growth_notes",))},
        {"type": "chapter", "title": "TUVAKI NI QELE NI TEITEI ENA LOMA NI JIKINA"},
        {"type": "section", "title": "6.1 Tuvaki ni Qele ni Teitei", "fields": _form_fields(form, ("has_registered_farmland", "farmland_lease_count", "farmland_acres_leased", "farmland_lease_years_covered", "farmland_development_notes"))},
        {"type": "chapter", "title": "VAKAITAVI NI VAKAILESILESI ENA BOSE NI JIKINA"},
        {"type": "section", "title": "7.0 Vakaitavi ni Vakailesilesi", "fields": _form_fields(form, ("reps_attend_meetings", "reps_understand_training_needs", "reps_assist_report_writing", "reps_help_outside_meetings", "reps_additional_notes", "reps_council_decision"))},
        {"type": "matrix", "key": "challenge_indicators", "title": MNT_FORMSET_TITLES["challenge_indicators"], "formset": formsets["challenge_indicators"], "rows": _matrix_rows(formsets["challenge_indicators"]), "column_labels": ["Toqa"]},
        {"type": "chapter", "title": "VEITALEVI ENA VEIKORO"},
        {"type": "formset", "key": "village_visits", "title": MNT_FORMSET_TITLES["village_visits"], "formset": formsets["village_visits"]},
    ]
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
    labels = MNTReportForm.Meta.labels
    return [(title, [_field_value(report, report._meta.get_field(name), labels) for name in names]) for title, names in MNT_SECTIONS]


CHILD_SECTION_FIELDS = {
    "savings_accounts": ("funds_held", "bank"),
}


def _model_rows(items, field_names=None):
    rows = []
    for item in items:
        labels = DETAIL_LABELS_BY_MODEL.get(item._meta.model.__name__, {})
        if field_names:
            fields = [item._meta.get_field(name) for name in field_names]
        else:
            fields = [field for field in item._meta.fields if field.name not in {"id", "report"}]
        rows.append([_field_value(item, field, labels) for field in fields])
    return rows


def _child_sections(report):
    return [(MNT_FORMSET_TITLES[key], _model_rows(getattr(report, related).all(), CHILD_SECTION_FIELDS.get(key))) for key, related in (
        ("koro_under_tikina", "koro_under_tikina"),
        ("vagalala_settlements", "vagalala_settlements"),
        ("settlement_registrations", "settlement_registrations"),
        ("coordination_status", "coordination_statuses"),
        ("disputes", "disputes"),
        ("social_indicators", "social_indicators"),
        ("education_trainings", "education_trainings"),
        ("income_sources", "income_sources"),
        ("tree_planting", "tree_planting_trainings"),
        ("income_activities", "income_activities"),
        ("savings_accounts", "savings_accounts"),
        ("fund_challenges", "fund_challenges"),
        ("challenge_indicators", "challenge_indicators"),
        ("village_visits", "village_visits"),
    )]


def can_edit_report(user, report):
    return report.owner_id == user.id and report.status in {
        MNTReport.STATUS_DRAFT,
        MNTReport.STATUS_RETURNED_BY_ROKO,
    }


def can_export_report(report):
    return report.status == MNTReport.STATUS_APPROVED_BY_ROKO


def workflow_actions_for(user, report):
    if not is_roko_user(user):
        return []
    if report.status == MNTReport.STATUS_SUBMITTED_TO_ROKO:
        actions = [
            MNTApprovalAction.ACTION_APPROVE,
            MNTApprovalAction.ACTION_RETURN,
            MNTApprovalAction.ACTION_REJECT,
            MNTApprovalAction.ACTION_COMMENT,
        ]
    else:
        actions = [MNTApprovalAction.ACTION_COMMENT] if report.status != MNTReport.STATUS_DRAFT else []
    return [{"type": action, "label": ACTION_LABELS[action]} for action in actions]


def next_status_for_action(report, action_type):
    if action_type == MNTApprovalAction.ACTION_COMMENT:
        return report.status
    if report.status != MNTReport.STATUS_SUBMITTED_TO_ROKO:
        raise ValidationError("This report is not waiting for Roko Tui approval.")
    if action_type == MNTApprovalAction.ACTION_APPROVE:
        return MNTReport.STATUS_APPROVED_BY_ROKO
    if action_type == MNTApprovalAction.ACTION_RETURN:
        return MNTReport.STATUS_RETURNED_BY_ROKO
    if action_type == MNTApprovalAction.ACTION_REJECT:
        return MNTReport.STATUS_REJECTED_BY_ROKO
    raise ValidationError("Invalid approval workflow action.")


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_approval_action(request, report, action_type, comment="", to_status=None, from_status=None):
    if action_type != MNTApprovalAction.ACTION_SUBMIT and not is_roko_user(request.user):
        raise PermissionDenied
    from_status = from_status if from_status is not None else report.status
    to_status = to_status if to_status is not None else next_status_for_action(report, action_type)
    if to_status != report.status:
        report.status = to_status
        report.save(update_fields=["status", "updated_at"])
    user_name = request.user.get_full_name().strip() or request.user.get_username()
    action_label = dict(MNTApprovalAction.ACTION_CHOICES).get(action_type, action_type).lower()
    acknowledgement = f"I, {user_name}, acting as {'Roko Tui' if is_roko_user(request.user) else 'Mata ni Tikina'}, confirm that I reviewed this report and performed this action ({action_label}) on {timezone.localtime(timezone.now()).strftime('%d %b %Y %H:%M')}."
    return MNTApprovalAction.objects.create(
        report=report,
        user=request.user,
        user_full_name=user_name,
        user_role="Roko Tui" if is_roko_user(request.user) else "Mata ni Tikina",
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
    status_labels = dict(MNTReport.STATUS_CHOICES)
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
        form = MNTReportForm(post_data, instance=report)
        formsets = _get_mnt_formsets(data=post_data, instance=report)
        present_formsets = _bound_formsets(formsets)
        if form.is_valid() and all(formset.is_valid() for formset in present_formsets):
            action = request.POST.get("action", "save_draft")
            with transaction.atomic():
                report = form.save(commit=False)
                original_status = report.status
                _refresh_report_auto_totals(report)
                if action == "submit_report":
                    report.submit()
                elif report.status != MNTReport.STATUS_RETURNED_BY_ROKO:
                    report.status = MNTReport.STATUS_DRAFT
                    report.submitted_at = None
                report.save()
                for formset in present_formsets:
                    formset.instance = report
                    formset.save()
                _ensure_koro_rows_for_tikina(report)
                _refresh_report_auto_totals(report)
                report.save(update_fields=["tikina_population", "council_total_attendees", "vagalala_population_total", "vagalala_family_total", "updated_at"])
                if action == "submit_report":
                    record_approval_action(
                        request,
                        report,
                        MNTApprovalAction.ACTION_SUBMIT,
                        comment="Report submitted for Roko Tui approval.",
                        to_status=report.status,
                        from_status=original_status,
                    )
            if action == "submit_report":
                messages.success(request, "Sa vakau na iVolavola ni Mata ni Tikina.")
                return redirect("mata_ni_tikina:report_detail", pk=report.pk)
            messages.success(request, "Sa maroroi na draft.")
            return redirect("mata_ni_tikina:report_edit", pk=report.pk)
    else:
        _refresh_report_auto_totals(report)
        form = MNTReportForm(instance=report)
        formsets = _get_mnt_formsets(instance=report if report.pk else None, initial_seeds=initial_seeds, tikina_name=report.tikina)
    return render(request, "mata_ni_tikina/report_form.html", {"form": form, "form_blocks": _report_form_blocks(form, formsets), "profile": profile, "report": report if report.pk else None})


@membership_required(TuragaProfile.MATA_NI_TIKINA, allow_roko=True)
def report_list(request):
    return render(request, "mata_ni_tikina/report_list.html", {"reports": reports_for(request.user).order_by("-year", "-created_at")})


@membership_required(TuragaProfile.MATA_NI_TIKINA, allow_roko=True)
def report_create(request):
    owner_profile, response = resolve_report_owner(request, TuragaProfile.MATA_NI_TIKINA, "mata_ni_tikina:report_create")
    if response:
        return response
    profile, defaults = _profile_report_defaults(owner_profile.user)
    return _handle_report_form(request, MNTReport(**defaults), profile, initial_seeds=True)


@membership_required(TuragaProfile.MATA_NI_TIKINA, allow_roko=True)
def report_edit(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not can_edit_report(request.user, report):
        messages.error(request, "Sa tiko na ripote qo ena kena dikevi ka sega ni rawa ni veisautaki.")
        return redirect("mata_ni_tikina:report_detail", pk=report.pk)
    profile, _ = _profile_report_defaults(report.owner or request.user)
    return _handle_report_form(request, report, profile)


@membership_required(TuragaProfile.MATA_NI_TIKINA, allow_roko=True)
def report_detail(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    return render(request, "mata_ni_tikina/report_detail.html", {
        "report": report,
        "stats": [("Koro", report.total_villages_under_buli()), ("Veileti", report.total_disputes()), ("Soli", report.soli_collected_amount or 0), ("Veisiko", report.village_visits.count())],
        "sections": _detail_sections(report),
        "child_sections": _child_sections(report),
        "approval_actions": report.approval_actions.select_related("user"),
        "workflow_actions": workflow_actions_for(request.user, report),
        "approval_form": ApprovalActionForm(),
        "can_edit_report": can_edit_report(request.user, report),
        "can_export_report": can_export_report(report),
    })


@membership_required(TuragaProfile.MATA_NI_TIKINA, TuragaProfile.ROKO, allow_roko=True)
@require_POST
def report_workflow_action(request, pk, action_type):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not is_roko_user(request.user):
        raise PermissionDenied
    form = ApprovalActionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please confirm the digital acknowledgement before continuing.")
        return redirect("mata_ni_tikina:report_detail", pk=report.pk)
    try:
        record_approval_action(
            request,
            report,
            action_type,
            comment=form.cleaned_data.get("comment", ""),
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if exc.messages else "Invalid workflow action.")
        return redirect("mata_ni_tikina:report_detail", pk=report.pk)
    messages.success(request, "The Roko Tui approval action was recorded.")
    return redirect("mata_ni_tikina:report_detail", pk=report.pk)


@membership_required(TuragaProfile.MATA_NI_TIKINA, allow_roko=True)
def report_pdf(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not can_export_report(report):
        messages.error(request, "E dodonu me vakadonui mada na ripote qo mai vua na Roko Tui ni bera ni export taki.")
        return redirect("mata_ni_tikina:report_detail", pk=report.pk)
    return report_pdf_response(
        title="Mata ni Tikina Quarterly Report",
        subtitle=f"{report.tikina} - {report.province} - {report.quarter} {report.year}",
        meta_rows=[
            ("iTutu", "Mata ni Tikina"),
            ("Yacamuni Taucoko", report.full_name),
            ("Jikina", report.tikina),
            ("Ripote ni vula ko", report.quarter),
            ("Ena yabaki ko", report.year),
            ("iTuvaki", report.get_status_display()),
            ("Siga ni vakau", report.submitted_at.strftime("%d %b %Y") if report.submitted_at else "-"),
        ],
        sections=_detail_sections(report),
        child_sections=_child_sections(report),
        audit_rows=_audit_trail_rows(report),
        filename=f"mata-ni-tikina-{report.tikina}-{report.quarter}-{report.year}.pdf".replace(" ", "-").lower(),
    )


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
    profile = getattr(request.user, "turaga_profile", None)
    tnk_review_queue = TNKReport.objects.none()
    if profile and profile.district:
        tnk_review_queue = TNKReport.objects.filter(
            district__iexact=profile.district,
            status=TNKReport.STATUS_SUBMITTED_TO_MATA,
        ).order_by("-year", "-created_at")
    return render(
        request,
        "mata_ni_tikina/dashboard.html",
        {
            "reports": reports[:5],
            "analysis": mnt_dashboard_analysis(reports),
            "reference_data": _reference_data(reports),
            "tnk_review_queue": tnk_review_queue,
        },
    )
