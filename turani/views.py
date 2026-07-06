from collections import OrderedDict

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import is_roko_user, membership_required
from accounts.models import TuragaProfile
from accounts.reporting import resolve_report_owner
from common.pdf_exports import report_pdf_response

from .analytics import tnk_dashboard_analysis
from .forms import (
    AssetSavingFormSet,
    BusinessFormSet,
    BusinessTrainingFormSet,
    CommitteeFormSet,
    CorrectionReturneeFormSet,
    CropFormSet,
    CulturalKnowledgeFormSet,
    DisabilityFormSet,
    ElectricityFormSet,
    EvacuationMaterialFormSet,
    FIJIAN_INLINE_LABELS,
    HealthConditionFormSet,
    HousingFormSet,
    IVDPProjectFormSet,
    IVDPScheduleFormSet,
    LawOffenceFormSet,
    MeetingDecisionFormSet,
    PopulationFormSet,
    ApprovalActionForm,
    TNK_SECTIONS,
    TNKReportForm,
    ToiletTypeFormSet,
    TraditionalTitleFormSet,
    TrainingFormSet,
    VisitFormSet,
    WasteManagementForm,
    WaterCommitteeMemberFormSet,
    WaterCommitteeQuestionFormSet,
    WaterSourceFormSet,
)

from .models import (
    Business,
    BusinessTraining,
    ElectricitySource,
    EvacuationCentreMaterial,
    HealthConditionCount,
    HousingCount,
    IVDPProject,
    LawOffence,
    PopulationAgeGroup,
    TNKApprovalAction,
    TNKReport,
    ToiletType,
    TraditionalTitleStatus,
    VillageAssetSaving,
    VillageCommittee,
    WasteManagement,
    WaterCommitteeQuestion,
    WaterSource,
)
from .workflow import (
    allowed_actions,
    can_edit_report,
    can_view_report,
    record_action,
    role_for_user,
    visible_reports_for,
)


REPORT_PREFETCHES = (
    "visits",
    "meeting_decisions",
    "committees",
    "law_offences",
    "correction_returnees",
    "trainings",
    "population",
    "housing_counts",
    "water_sources",
    "water_committee_answers",
    "water_committee_members",
    "toilet_types",
    "electricity_sources",
    "health_conditions",
    "disabilities",
    "crops",
    "ivdp_projects",
    "ivdp_schedule",
    "businesses",
    "business_trainings",
    "assets_savings",
    "evacuation_centre_materials",
    "traditional_titles",
    "cultural_knowledge",
)


DETAIL_FORMSETS = (
    VisitFormSet,
    MeetingDecisionFormSet,
    CommitteeFormSet,
    LawOffenceFormSet,
    CorrectionReturneeFormSet,
    TrainingFormSet,
    PopulationFormSet,
    HousingFormSet,
    WaterSourceFormSet,
    WaterCommitteeQuestionFormSet,
    WaterCommitteeMemberFormSet,
    ToiletTypeFormSet,
    ElectricityFormSet,
    HealthConditionFormSet,
    DisabilityFormSet,
    CropFormSet,
    IVDPProjectFormSet,
    IVDPScheduleFormSet,
    BusinessFormSet,
    BusinessTrainingFormSet,
    AssetSavingFormSet,
    EvacuationMaterialFormSet,
    TraditionalTitleFormSet,
    CulturalKnowledgeFormSet,
)


DETAIL_LABELS_BY_MODEL = {
    formset.model.__name__: {
        **FIJIAN_INLINE_LABELS.get(formset.model.__name__, {}),
        **(getattr(formset.form._meta, "labels", None) or {}),
    }
    for formset in DETAIL_FORMSETS
}
DETAIL_LABELS_BY_MODEL["WasteManagement"] = WasteManagementForm.Meta.labels


def reports_for(user):
    return visible_reports_for(user).prefetch_related(*REPORT_PREFETCHES)


def _get_tnk_formsets(data=None, instance=None, initial_seeds=False):
    def kwargs_for(prefix):
        kwargs = {"instance": instance}

        if data is not None and f"{prefix}-TOTAL_FORMS" in data:
            kwargs["data"] = data

        return kwargs

    formsets = OrderedDict(
        [
            ("visits", VisitFormSet(**kwargs_for("visits"), prefix="visits")),
            ("decisions", MeetingDecisionFormSet(**kwargs_for("decisions"), prefix="decisions")),
            ("committees", CommitteeFormSet(**kwargs_for("committees"), prefix="committees")),
            ("law_offences", LawOffenceFormSet(**kwargs_for("law"), prefix="law")),
            ("returnees", CorrectionReturneeFormSet(**kwargs_for("returnees"), prefix="returnees")),
            ("trainings", TrainingFormSet(**kwargs_for("trainings"), prefix="trainings")),
            ("population", PopulationFormSet(**kwargs_for("pop"), prefix="pop")),
            ("housing", HousingFormSet(**kwargs_for("housing"), prefix="housing")),
            ("water_sources", WaterSourceFormSet(**kwargs_for("wsrc"), prefix="wsrc")),
            ("water_q", WaterCommitteeQuestionFormSet(**kwargs_for("wq"), prefix="wq")),
            ("water_members", WaterCommitteeMemberFormSet(**kwargs_for("wm"), prefix="wm")),
            ("toilets", ToiletTypeFormSet(**kwargs_for("toilet"), prefix="toilet")),
            ("electricity", ElectricityFormSet(**kwargs_for("elec"), prefix="elec")),
            ("health", HealthConditionFormSet(**kwargs_for("health"), prefix="health")),
            ("disabilities", DisabilityFormSet(**kwargs_for("disab"), prefix="disab")),
            ("crops", CropFormSet(**kwargs_for("crops"), prefix="crops")),
            ("ivdp_projects", IVDPProjectFormSet(**kwargs_for("ivdp"), prefix="ivdp")),
            ("ivdp_schedule", IVDPScheduleFormSet(**kwargs_for("sched"), prefix="sched")),
            ("businesses", BusinessFormSet(**kwargs_for("biz"), prefix="biz")),
            ("business_trainings", BusinessTrainingFormSet(**kwargs_for("biztrain"), prefix="biztrain")),
            ("assets", AssetSavingFormSet(**kwargs_for("assets"), prefix="assets")),
            ("evacuation", EvacuationMaterialFormSet(**kwargs_for("evac"), prefix="evac")),
            ("titles", TraditionalTitleFormSet(**kwargs_for("titles"), prefix="titles")),
            ("culture", CulturalKnowledgeFormSet(**kwargs_for("culture"), prefix="culture")),
        ]
    )

    if initial_seeds and instance is None and data is None:
        formsets["committees"] = CommitteeFormSet(
            prefix="committees",
            initial=[
                {"committee_type": value}
                for value, _ in VillageCommittee.COMMITTEE_TYPES
            ],
        )

        formsets["law_offences"] = LawOffenceFormSet(
            prefix="law",
            initial=[
                {"offence_name": label}
                for _, label in LawOffence.OFFENCE_TYPES
            ],
        )

        formsets["population"] = PopulationFormSet(
            prefix="pop",
            initial=[
                {"gender": gender, "age_group": age_group}
                for gender, _ in PopulationAgeGroup.GENDER
                for age_group, _ in PopulationAgeGroup.AGE_GROUP
            ],
        )

        formsets["housing"] = HousingFormSet(
            prefix="housing",
            initial=[
                {"house_type": house_type, "material": material}
                for house_type, _ in HousingCount.HOUSE_TYPE
                for material, _ in HousingCount.MATERIAL
            ],
        )

        formsets["water_sources"] = WaterSourceFormSet(
            prefix="wsrc",
            initial=[
                {"source": value}
                for value, _ in WaterSource.SOURCE
            ],
        )

        formsets["water_q"] = WaterCommitteeQuestionFormSet(
            prefix="wq",
            initial=[
                {"question": label}
                for _, label in WaterCommitteeQuestion.QUESTIONS
            ],
        )

        formsets["assets"] = AssetSavingFormSet(
            prefix="assets",
            initial=[
                {"question": question}
                for _, question in VillageAssetSaving.QUESTIONS
            ],
        )

        formsets["toilets"] = ToiletTypeFormSet(
            prefix="toilet",
            initial=[
                {"toilet_type": value}
                for value, _ in ToiletType.TOILET_TYPE
            ],
        )

        formsets["electricity"] = ElectricityFormSet(
            prefix="elec",
            initial=[
                {"source": value}
                for value, _ in ElectricitySource.SOURCE
            ],
        )

        formsets["evacuation"] = EvacuationMaterialFormSet(
            prefix="evac",
            initial=[
                {"material": value}
                for value, _ in EvacuationCentreMaterial.MATERIAL
            ],
        )

        formsets["titles"] = TraditionalTitleFormSet(
            prefix="titles",
            initial=[
                {"title_type": value}
                for value, _ in TraditionalTitleStatus.TITLE_TYPE
            ],
        )

    return formsets


def _profile_report_defaults(user):
    profile, _ = TuragaProfile.objects.get_or_create(user=user)

    return profile, {
        "owner": user,
        "village": profile.village,
        "district": profile.district,
        "province": profile.province,
        "village_headman_name": profile.full_name,
        "village_headman_age": profile.age,
        "appointment_month_year": profile.appointment_date.strftime("%B %Y")
        if profile.appointment_date
        else "",
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


def _matrix_rows(formset, row_choices, column_count):
    forms = list(formset.forms)
    return [
        (label, forms[index * column_count : (index + 1) * column_count])
        for index, (_, label) in enumerate(row_choices)
    ]


def _report_form_blocks(form, waste_form, formsets):
    """
    This controls the visible order of the report form.

    To move a section, move its whole block up or down in this list.
    """

    return [
        {"type": "chapter", "title": "ULUTAGA 1: VEILIUTAKI VINAKA"},
        {
            "type": "section",
            "title": "1.0 Tukutuku me Baleti Turaga ni Koro"
            "",
            "show_required_errors": True,
            "fields": _form_fields(
                form,
                (
                    "quarter",
                    "year",
                    "village",
                    "district",
                    "province",
                    "village_headman_name",
                    "village_headman_age",
                    "appointment_month_year",
                ),
            ),
        },

        {
            "type": "formset",
            "key": "visits",
            "title": "1.1 Veisiko ena Valevolavola ni Yasana kei na Veitabana tale eso",
            "formset": formsets["visits"],
        },

        {
            "type": "section",
            "title": "2.0 Nai TUKUTUKU ni Bose Vakoro",
            "fields": _form_fields(
                form,
                (
                    "village_meetings_count",
                ),
            ),
        },

        {
            "type": "formset",
            "key": "decisions",
            "title": "2.0 Na Cava Soti na Veilewa Bibi e Tau Kina?",
            "formset": formsets["decisions"],
            "allow_add": True,
        },

        {
            "type": "formset",
            "key": "committees",
            "title": "2.1 Na Komiti Cava Soti e Ra Tiko ena Koro ena Gauna Oqo",
            "formset": formsets["committees"],
        },

        {
            "type": "formset",
            "key": "law_offences",
            "title": "3.0 Basuki ni Lawa ni Matanitu",
            "formset": formsets["law_offences"],
        },

        {
            "type": "formset",
            "key": "returnees",
            "title": "4.0 Vakacokotaki ni Gone Suka Mai na Tabana ni Veivakadodonutaki",
            "formset": formsets["returnees"],
            "allow_add": True,
        },

        {
            "type": "section",
            "title": "4.1 Tuvatuva me Baleti Ira na Suka Mai na Vale ni Veivakadodonutaki",
            "fields": _form_fields(
                form,
                (
                    "correction_reintegration_plan",
                ),
            ),
        },

        {
            "type": "formset",
            "key": "trainings",
            "title": "5.0 Na Vuli ni Veituberi / Veivakararamataki",
            "formset": formsets["trainings"],
        },

        {"type": "chapter", "title": "ULUTAGA 2: TIKO VINAKA NI iTAUKEI"},
        {
            "type": "matrix",
            "key": "population",
            "title": "6.0 Na Lewe ni Koro",
            "formset": formsets["population"],
            "column_labels": [label for _, label in PopulationAgeGroup.AGE_GROUP],
            "rows": _matrix_rows(
                formsets["population"],
                PopulationAgeGroup.GENDER,
                len(PopulationAgeGroup.AGE_GROUP),
            ),
            "show_totals": True,
        },

        {
            "type": "household",
            "title": "6.1 Nai wiliwili ni matavuvale era tiko ena loma ni koro",
            "field": form["household_count"],
        },

        {
            "type": "matrix",
            "key": "housing",
            "title": "7.0 Na Veivakavaletaki ena Koro",
            "formset": formsets["housing"],
            "column_labels": [label for _, label in HousingCount.MATERIAL],
            "rows": _matrix_rows(
                formsets["housing"],
                HousingCount.HOUSE_TYPE,
                len(HousingCount.MATERIAL),
            ),
            "show_totals": True,
        },

        {
            "type": "formset",
            "key": "water_sources",
            "title": "8.0 Na Wai ni Gunu kei na Tiko Savasava",
            "formset": formsets["water_sources"],
        },

        {
            "type": "formset",
            "key": "water_q",
            "title": "8.0 Na Komiti ni Wai ni Koro",
            "formset": formsets["water_q"],
        },

        {
            "type": "section",
            "title": "8.1 Ni Dau Leqa na Wai, na Tabana Cava e Dau Mai Qarava?",
            "fields": _form_fields(
                form,
                (
                    "water_challenges",
                    "water_problem_responsible_agency",
                ),
            ),
        },

        {
            "type": "formset",
            "key": "water_members",
            "title": "8.2 Na Yacadra na Lewe ni Komiti ni Wai ena Loma ni Koro",
            "formset": formsets["water_members"],
        },

        {
            "type": "section",
            "title": "8.3 Bolebole se Dredre ena Maroroi ni Wai kei na Tiko Savasava",
            "fields": _form_fields(form, ("water_sanitation_challenges",)),
        },

        {
            "type": "waste",
            "title": "8.4 Na Maroroi ni Benu",
            "form": waste_form,
        },

        {
            "type": "formset",
            "key": "toilets",
            "title": "9.0 Na Vale Lailai kei na Vakadrodroi ni Wai e Loma ni Koro",
            "formset": formsets["toilets"],
        },

        {
            "type": "section",
            "title": "9.2 Ni dau leqa na Vakadrodroi tani ni Wai ni Vale Lailai, se vuabale",
            "fields": _form_fields(
                form,
                ("toilet_wastewater_challenges", "toilet_wastewater_agency"),
            ),
        },

        {
            "type": "formset",
            "key": "electricity",
            "title": "10.0 Na Veivakalivalivataki",
            "formset": formsets["electricity"],
        },

        {
            "type": "formset",
            "key": "health",
            "title": "11.0 Na Mate Veitauvi",
            "formset": formsets["health"],
        },

        {
            "type": "formset",
            "key": "disabilities",
            "title": "11.2 Malumalumu ni Tuvaki ni Yago",
            "formset": formsets["disabilities"],
        },

        {
            "type": "formset",
            "key": "crops",
            "title": "11.3 & 11.4 Na Kakana Draudrau kei na Kakana Dina",
            "formset": formsets["crops"],
        },

        {
            "type": "section",
            "title": "12.0 Na Veiqaravi ni Tuvatuva ni Veivakatorocaketaki Raraba ni Koro (IVDP)",
            "fields": _form_fields(
                form,
                (
                    "ivdp_progress_started",
                    "ivdp_unfinished_reason",
                ),
            ),
        },

        {
            "type": "formset",
            "key": "ivdp_projects",
            "title": "12.1 Tuvatuva ni Veivakatorocaketaki Raraba ni Koro",
            "formset": formsets["ivdp_projects"],
        },

        {"type": "chapter", "title": "ULUTAGA 3: NA BULA TOROCAKE NI iTAUKEI"},
        {"type": "label", "title": "13.0 Bisinisi"},
        {
            "type": "formset",
            "key": "business_trainings",
            "title": "13.1 Na Vuli ni Cicivaki Bisinisi / Vakatubui Lavo ena Vula Tolu Sa Oti",
            "formset": formsets["business_trainings"],
        },

        {
            "type": "formset",
            "key": "businesses",
            "title": "13.2 Na Bisinisi Vakaitaukei Cava sa Tiko Rawa ena Koro",
            "formset": formsets["businesses"],
        },

        {
            "type": "formset",
            "key": "assets",
            "title": "13.3 Na Maroroi ni Yau / Lavo ni Koro",
            "formset": formsets["assets"],
        },

        {"type": "chapter", "title": "ULUTAGA 4: TAQOMAKI NI IYAUBULA KEI NA LEQA TUBUKOSO"},
        {
            "type": "section",
            "title": "14.0 Yau Bula",
            "fields": _form_fields(
                form,
                (
                    "yaubula_current_plan",
                    "yaubula_management_plan",
                ),
            ),
        },

        {
            "type": "section",
            "title": "15.0 Leqa Tubukoso",
            "fields": _form_fields(
                form,
                (
                    "disaster_current_plan",
                    "disaster_future_plan",
                ),
            ),
        },

        {
            "type": "section",
            "title": "15.1 Vale ni Dro kei na Draki Veisau",
            "fields": _form_fields(
                form,
                (
                    "has_evacuation_centre",
                    "evacuation_centre_capacity",
                    "has_male_female_restrooms",
                ),
            ),
        },

        {
            "type": "formset",
            "key": "evacuation",
            "title": "15.1 Vale ni Dro - iYaya e Vakayagataki",
            "formset": formsets["evacuation"],
        },

        {
            "type": "section",
            "title": "15.1 & 16.0 Revurevu ni Draki Veisau kei na Kena i Wali",
            "fields": _form_fields(
                form,
                (
                    "climate_change_impact",
                    "climate_change_impact_details",
                    "climate_change_solution_done",
                    "climate_change_solution_details",
                ),
            ),
        },

        {"type": "chapter", "title": "ULUTAGA 5: NA VAQAQACOTAKI NI VANUA KEI NA KENA VEILIUTAKI"},
        {"type": "label", "title": "17.0 Veiliutaki Vakavanua"},
        {
            "type": "section",
            "title": "17.1 E dabe vakavica Na Bose ni Vanua ena Vula 3 Sa Oti?",
            "fields": _form_fields(form, ("bose_vanua_count",)),
        },
        {
            "type": "formset",
            "key": "titles",
            "title": "17.2 Nai Tutu Vakavanua e Vakadeitaki ena Vula 3 Sa Oti",
            "formset": formsets["titles"],
        },

        {
            "type": "formset",
            "key": "culture",
            "title": "18.0 Na Maroroi ni Tovo / Vakarau Vakavanua",
            "formset": formsets["culture"],
        },

        {
            "type": "formset",
            "key": "ivdp_schedule",
            "title": "Tuvatuva ni Vakayacori ni IVDP ni Koro",
            "formset": formsets["ivdp_schedule"],
        },
    ]


def _section_forms(form):
    return [
        (title, [form[name] for name in names if name in form.fields])
        for title, names in TNK_SECTIONS
    ]


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
    sections = []
    labels = TNKReportForm.Meta.labels

    for title, names in TNK_SECTIONS:
        items = []

        for name in names:
            field = report._meta.get_field(name)
            items.append(_field_value(report, field, labels))

        sections.append((title, items))

    return sections


def _model_rows(items):
    rows = []

    for item in items:
        values = []
        labels = DETAIL_LABELS_BY_MODEL.get(item._meta.model.__name__, {})

        for field in item._meta.fields:
            if field.name in {"id", "report"}:
                continue

            values.append(_field_value(item, field, labels))

        rows.append(values)

    return rows


def _child_sections(report):
    return [
        ("Veisiko", _model_rows(report.visits.all())),
        ("Lewani ni Bose Vakoro", _model_rows(report.meeting_decisions.all())),
        ("Komiti ni Koro", _model_rows(report.committees.all())),
        ("Lawa kei na Veivakacalai", _model_rows(report.law_offences.all())),
        ("Lesu mai na Veivakadodonutaki", _model_rows(report.correction_returnees.all())),
        ("Vuli", _model_rows(report.trainings.all())),
        ("Tagane-Marama", _model_rows(report.population.all())),
        ("Vale", _model_rows(report.housing_counts.all())),
        ("Vurevure ni Wai", _model_rows(report.water_sources.all())),
        ("Taro ni Komiti ni Wai", _model_rows(report.water_committee_answers.all())),
        ("Lewe ni Komiti ni Wai", _model_rows(report.water_committee_members.all())),
        ("Mataqali Valelailai", _model_rows(report.toilet_types.all())),
        ("Livaliva", _model_rows(report.electricity_sources.all())),
        ("Tiko Bulabula", _model_rows(report.health_conditions.all())),
        ("Vakaleqai ni Yago", _model_rows(report.disabilities.all())),
        ("Teitei", _model_rows(report.crops.all())),
        ("Tuvatuva ni Veivakatorocaketaki Raraba ni Koro", _model_rows(report.ivdp_projects.all())),
        ("Tuvatuva ni IVDP", _model_rows(report.ivdp_schedule.all())),
        ("Bisinisi", _model_rows(report.businesses.all())),
        ("Vuli ni Bisinisi", _model_rows(report.business_trainings.all())),
        ("Yau kei na Maroroi", _model_rows(report.assets_savings.all())),
        ("Vale ni Dro", _model_rows(report.evacuation_centre_materials.all())),
        ("iTutu Vakavanua", _model_rows(report.traditional_titles.all())),
        ("Kilaka Vakavanua", _model_rows(report.cultural_knowledge.all())),
    ]


def _audit_trail_rows(report):
    rows = []
    status_labels = dict(TNKReport.STATUS_CHOICES)
    for action in report.approval_actions.select_related("user"):
        rows.append(
            [
                ("iTavi e Qaravi", action.get_action_type_display()),
                ("Vakailesilesi", action.user_full_name),
                ("iTutu", action.user_role),
                ("iTuvaki e Liu", status_labels.get(action.from_status, action.from_status or "-")),
                ("iTuvaki Vou", status_labels.get(action.to_status, action.to_status or "-")),
                ("Vakamacala", action.comment or "-"),
                ("Vakadinadina Vakadigital", action.digital_acknowledgement),
                ("Siga kei na Gauna", timezone.localtime(action.created_at).strftime("%d %b %Y %H:%M")),
            ]
        )
    return rows


def _waste_instance(report):
    if not report.pk:
        return None

    try:
        return report.waste_management
    except WasteManagement.DoesNotExist:
        return None


def _handle_report_form(request, report, profile, *, initial_seeds=False):
    if request.method == "POST":
        post_data = _with_missing_defaults(request.POST, report)

        form = TNKReportForm(post_data, instance=report)
        waste_form = WasteManagementForm(post_data, instance=_waste_instance(report))
        formsets = _get_tnk_formsets(data=post_data, instance=report)
        present_formsets = _bound_formsets(formsets)

        if (
            form.is_valid()
            and waste_form.is_valid()
            and all(formset.is_valid() for formset in present_formsets)
        ):
            action = request.POST.get("action", "save_draft")

            with transaction.atomic():
                report = form.save(commit=False)

                original_status = report.status
                was_returned = original_status == TNKReport.STATUS_RETURNED_TO_TURAGA

                if action == "submit_report":
                    report.submit()
                elif report.status != TNKReport.STATUS_RETURNED_TO_TURAGA:
                    report.status = TNKReport.STATUS_DRAFT
                    report.submitted_at = None

                report.save()
                form.save_m2m()

                for formset in present_formsets:
                    formset.instance = report
                    formset.save()

                waste = waste_form.save(commit=False)
                waste.report = report
                waste.save()

                if action == "submit_report":
                    comment = "Report resubmitted after correction." if was_returned else "Report submitted for Mata ni Tikina review."
                    record_action(
                        request,
                        report,
                        TNKApprovalAction.ACTION_SUBMIT,
                        comment=comment,
                        to_status=report.status,
                        from_status=original_status,
                    )

            if action == "submit_report":
                messages.success(request, "Sa vakau na iVolavola ni Turaga ni Koro.")
                return redirect("turani:report_detail", pk=report.pk)

            messages.success(
                request,
                "Sa maroroi na draft. E rawa ni tomani tale ena loma ni vula tolu ni ripote.",
            )
            return redirect("turani:report_edit", pk=report.pk)

    else:
        form = TNKReportForm(instance=report)
        waste_form = WasteManagementForm(instance=_waste_instance(report))
        formsets = _get_tnk_formsets(instance=report if report.pk else None, initial_seeds=initial_seeds)

    context = {
        "form": form,
        "form_blocks": _report_form_blocks(form, waste_form, formsets),
        "profile": profile,
        "report": report if report.pk else None,
    }

    return render(request, "turani/report_form.html", context)


@membership_required(TuragaProfile.TURAGA_NI_KORO, TuragaProfile.MATA_NI_TIKINA, TuragaProfile.TURAGA_NI_YAVUSA, TuragaProfile.ROKO, allow_roko=True)
def report_list(request):
    reports = reports_for(request.user).order_by("-year", "-created_at")

    return render(
        request,
        "turani/report_list.html",
        {
            "reports": reports,
        },
    )


@membership_required(TuragaProfile.TURAGA_NI_KORO, allow_roko=True)
def report_create(request):
    owner_profile, response = resolve_report_owner(request, TuragaProfile.TURAGA_NI_KORO, "turani:report_create")
    if response:
        return response
    profile, defaults = _profile_report_defaults(owner_profile.user)
    report = TNKReport(**defaults)

    return _handle_report_form(request, report, profile, initial_seeds=True)


@membership_required(TuragaProfile.TURAGA_NI_KORO, allow_roko=True)
def report_edit(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not can_edit_report(request.user, report):
        messages.error(request, "This report is locked for review and cannot be edited.")
        return redirect("turani:report_detail", pk=report.pk)
    profile, _ = _profile_report_defaults(report.owner or request.user)

    return _handle_report_form(request, report, profile)


@membership_required(TuragaProfile.TURAGA_NI_KORO, TuragaProfile.MATA_NI_TIKINA, TuragaProfile.TURAGA_NI_YAVUSA, TuragaProfile.ROKO, allow_roko=True)
def report_detail(request, pk):
    report = get_object_or_404(
        reports_for(request.user).select_related("waste_management"),
        pk=pk,
    )
    if not can_view_report(request.user, report):
        raise PermissionDenied

    context = {
        "report": report,
        "stats": [
            ("Tagane-Marama", report.total_population()),
            ("Vuvale", report.household_count),
            ("Basuki ni Lawa", report.total_offences()),
            ("Tuvatuva ni IVDP", report.total_ivdp_projects()),
        ],
        "sections": _detail_sections(report),
        "child_sections": _child_sections(report),
        "approval_actions": report.approval_actions.select_related("user"),
        "workflow_actions": allowed_actions(request.user, report),
        "approval_form": ApprovalActionForm(),
        "can_edit_report": can_edit_report(request.user, report),
    }

    return render(request, "turani/report_detail.html", context)


@membership_required(TuragaProfile.TURAGA_NI_KORO, TuragaProfile.MATA_NI_TIKINA, TuragaProfile.TURAGA_NI_YAVUSA, TuragaProfile.ROKO, allow_roko=True)
@require_POST
def report_workflow_action(request, pk, action_type):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not can_view_report(request.user, report):
        raise PermissionDenied

    form = ApprovalActionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please confirm the digital acknowledgement before continuing.")
        return redirect("turani:report_detail", pk=report.pk)

    try:
        record_action(
            request,
            report,
            action_type,
            comment=form.cleaned_data.get("comment", ""),
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if exc.messages else "Invalid workflow action.")
        return redirect("turani:report_detail", pk=report.pk)

    messages.success(request, "The approval action was recorded in the audit trail.")
    return redirect("turani:report_detail", pk=report.pk)


@membership_required(TuragaProfile.TURAGA_NI_KORO, TuragaProfile.MATA_NI_TIKINA, TuragaProfile.TURAGA_NI_YAVUSA, TuragaProfile.ROKO, allow_roko=True)
def approval_timeline(request, pk):
    report = get_object_or_404(reports_for(request.user), pk=pk)
    if not can_view_report(request.user, report):
        raise PermissionDenied
    return render(
        request,
        "turani/approval_timeline.html",
        {
            "report": report,
            "approval_actions": report.approval_actions.select_related("user"),
        },
    )


@membership_required(TuragaProfile.TURAGA_NI_KORO, TuragaProfile.MATA_NI_TIKINA, TuragaProfile.TURAGA_NI_YAVUSA, TuragaProfile.ROKO, allow_roko=True)
def report_pdf(request, pk):
    report = get_object_or_404(
        reports_for(request.user).select_related("waste_management"),
        pk=pk,
    )
    return report_pdf_response(
        title="Turaga ni Koro Quarterly Report",
        subtitle=f"{report.village} - {report.district} - {report.quarter} {report.year}",
        meta_rows=[
            ("iTutu", "Turaga ni Koro"),
            ("Koro", report.village),
            ("Tikina", report.district),
            ("Ripote ni vula ko", report.quarter),
            ("Ena yabaki ko", report.year),
            ("iTuvaki", report.get_status_display()),
            ("Siga ni vakau", report.submitted_at.strftime("%d %b %Y") if report.submitted_at else "-"),
        ],
        sections=_detail_sections(report),
        child_sections=_child_sections(report),
        audit_rows=_audit_trail_rows(report),
        filename=f"turaga-ni-koro-{report.village}-{report.quarter}-{report.year}.pdf".replace(" ", "-").lower(),
    )


@membership_required(TuragaProfile.TURAGA_NI_KORO, allow_roko=True)
def turaga_dashboard(request):
    reports = reports_for(request.user).order_by("-year", "-created_at")
    analysis = tnk_dashboard_analysis(reports)

    population = PopulationAgeGroup.objects.filter(report__in=reports)
    offences = LawOffence.objects.filter(report__in=reports)
    health = HealthConditionCount.objects.filter(report__in=reports)
    businesses = Business.objects.filter(report__in=reports)
    projects = IVDPProject.objects.filter(report__in=reports)

    context = {
        "total_reports": reports.count(),
        "total_population": population.aggregate(total=Sum("count"))["total"] or 0,
        "total_households": reports.aggregate(total=Sum("household_count"))["total"] or 0,
        "total_offences": offences.aggregate(total=Sum("count"))["total"] or 0,
        "total_health_cases": health.aggregate(total=Sum("count"))["total"] or 0,
        "total_businesses": businesses.count(),
        "total_ivdp_projects": projects.count(),

        "population_by_gender": population.values("gender")
        .annotate(total=Sum("count"))
        .order_by("gender"),

        "population_by_age": population.values("age_group")
        .annotate(total=Sum("count"))
        .order_by("age_group"),

        "offences_by_type": offences.values("offence_name")
        .annotate(total=Sum("count"))
        .order_by("-total"),

        "health_by_condition": health.values("condition_name")
        .annotate(total=Sum("count"))
        .order_by("-total"),

        "businesses_by_type": businesses.values("business_type")
        .annotate(total=Count("id"))
        .order_by("-total"),

        "ivdp_by_priority": projects.values("priority_area")
        .annotate(total=Count("id"))
        .order_by("priority_area"),

        "tnk_latest": reports[:5],
        "tnk_total": reports.count(),
        "tnk_quarters": reports.values("quarter", "year")
        .distinct()
        .order_by("-year", "quarter")[:8],
        "analysis": analysis,
        "workflow_queues": {
            "draft": reports.filter(status=TNKReport.STATUS_DRAFT),
            "returned": reports.filter(status=TNKReport.STATUS_RETURNED_TO_TURAGA),
            "submitted": reports.exclude(status__in=[TNKReport.STATUS_DRAFT, TNKReport.STATUS_RETURNED_TO_TURAGA, TNKReport.STATUS_FINAL_APPROVED]),
            "final": reports.filter(status=TNKReport.STATUS_FINAL_APPROVED),
        },
        "workflow_role": role_for_user(request.user),
    }

    return render(request, "turani/dashboard.html", context)
