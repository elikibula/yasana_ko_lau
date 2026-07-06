from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import (
    Business,
    BusinessTraining,
    CorrectionReturnee,
    CropCount,
    CulturalKnowledge,
    DisabilityCount,
    ElectricitySource,
    EvacuationCentreMaterial,
    HealthConditionCount,
    HousingCount,
    IVDPImplementationSchedule,
    IVDPProject,
    LawOffence,
    PopulationAgeGroup,
    TNKReport,
    ToiletType,
    TraditionalTitleStatus,
    Training,
    VillageAssetSaving,
    VillageCommittee,
    VillageMeetingDecision,
    Visit,
    WasteManagement,
    WaterCommitteeMember,
    WaterCommitteeQuestion,
    WaterSource,
)


INPUT = "w-full rounded border border-lau-navy/30 px-3 py-2 text-sm focus:ring-2 focus:ring-lau-gold focus:outline-none"
SELECT = INPUT + " bg-gray-100"
AREA = INPUT + " resize-y"
CHECKBOX = "h-4 w-4 rounded border-lau-navy/30 text-lau-gold focus:ring-lau-gold"
DATE_DISPLAY_FORMAT = "%d/%m/%Y"
DATE_INPUT_FORMATS = [DATE_DISPLAY_FORMAT, "%Y-%m-%d"]


FIJIAN_INLINE_LABELS = {
    "LawOffence": {
        "offence_name": "Na Lawa e Basuki",
        "count": "Wiliwili",
        "reported_to_law": "Ripotekaki kina Tabana ni Lawa?",
        "reason_not_reported": "Kevaka e Sega ni Ripotekaki, Na Cava na Vuna?",
    },
    "CorrectionReturnee": {
        "name": "Yaca ni Gone Suka Mai",
        "rehabilitation_done": "Na Veivakacokotaki sa Vakayacori Oti",
        "current_activity": "Na Cava e sa Qarava Tiko ena Gauna Oqo",
    },
    "Training": {
        "training_type": "Mataqali ni Vuli",
        "title": "Yaca ni Vuli",
        "organization": "Soqosoqo / Tabana e Qarava",
        "date": "Tiki ni Siga",
        "purpose": "Na Cava na iNaki ni Vuli",
        "participants_count": "Wiliwili ni Lewe ni Vuli",
        "outcome": "Na Cava na Votuka ni Vuli",
    },
    "PopulationAgeGroup": {
        "gender": "Wasewase",
        "age_group": "Yabaki ni Bula",
        "count": "Wiliwili",
    },
    "HousingCount": {
        "house_type": "Mataqali ni Vale",
        "material": "iYaya ni Vale",
        "count": "Wiliwili",
    },
    "WaterSource": {
        "source": "Vurevure ni Wai",
        "selected": "Toqa",
    },
    "WaterCommitteeQuestion": {
        "question": "Taro ni Komiti ni Wai",
        "answer": "Toqa",
    },
    "WaterCommitteeMember": {"name": "Yaca"},
    "ToiletType": {"toilet_type": "Mataqali Vale Lailai", "count": "Wiliwili"},
    "ElectricitySource": {"source": "Vurevure ni Livaliva", "house_count": "Wiliwili ni Vale"},
    "HealthConditionCount": {
        "condition_name": "Veimataqali Mate",
        "age_group": "Wasewase ni Yabaki",
        "count": "Wiliwili",
    },
    "DisabilityCount": {
        "disability_name": "Malumalumu ni Yago",
        "age_group": "Wasewase ni Yabaki",
        "count": "Wiliwili",
    },
    "CropCount": {
        "category": "Mataqali Kakana",
        "crop_name": "Yaca ni Kakana",
        "plantation_count": "Wiliwili ni Teitei",
    },
    "IVDPProject": {
        "project_name": "Tuvatuva Cava",
        "project_number": "Nai ka vica ni Tuvatuva",
        "priority_area": "Vatavata",
        "work_done": "Veika sa Qaravi Rawa",
        "application_prepared": "Sa Vakaraurautaki na Kerekere?",
        "funding_agency": "Tabana e Vakailavotaka",
        "materials_received": "Sa Ciqomi na Kena iYaya?",
        "problem_reason": "Na Vuna ni Leqa / Dredre",
        "solution": "Na Kenai Wali",
    },
    "IVDPImplementationSchedule": {
        "project": "Tuvatuva",
        "responsibility": "iTavi",
        "organization": "Soqosoqo",
        "start_date": "Siga ni Tekivu",
        "end_date": "Siga ni Cava",
        "consultation_approval": "Veivosaki / Vakadonui",
        "commencement": "Sa Tekivu",
        "priority_area_achieved_50": "50% ni Vatavata sa Rawati",
        "project_completion": "Sa Vakacavari na Tuvatuva",
    },
    "Business": {
        "business_name": "Yaca ni Bisinisi",
        "owner_name": "Taukei ni Bisinisi",
        "licensed": "Sa Vakailiseni?",
        "business_type": "Bisinisi cava e Cicivaki",
        "years_running": "Na Dede ni Gauna sa Cicivaki Kina na Bisinisi",
    },
    "BusinessTraining": {
        "course_name": "Yaca ni Vuli",
        "organization": "Tabana e Qarava",
        "date": "Tiki ni Siga",
        "purpose": "Na Cava na iNaki ni Vuli",
        "participants_count": "Wiliwili ni Lewe ni Vuli",
        "outcome": "Na Cava na Votuka ni Vuli",
    },
    "VillageAssetSaving": {
        "question": "Taro",
        "answer": "iSau",
        "description": "Vakamacala",
    },
    "EvacuationCentreMaterial": {"material": "iYaya", "selected": "Toqa"},
    "TraditionalTitleStatus": {
        "title_type": "iTutu Vakavanua",
        "yavusa_mataqali_count": "Wiliwili ni Yavusa / Mataqali",
        "confirmed_count": "Sa Vakadeitaki Oti",
        "unconfirmed_count": "Sega ni Vakadeitaki",
        "being_processed": "Sa Cakacakataki Tiko",
    },
    "CulturalKnowledge": {
        "knowledge_type": "Na Kilaka Cava?",
        "preservation_plan": "Tuvatuva ni Maroroi",
    },
}


def style_widget(field):
    widget = field.widget

    if isinstance(field, forms.DateField):
        field.input_formats = DATE_INPUT_FORMATS
        widget.format = DATE_DISPLAY_FORMAT

    if isinstance(widget, forms.CheckboxInput):
        widget.attrs.update({"class": CHECKBOX})
    elif isinstance(widget, forms.Select):
        widget.attrs.update({"class": SELECT})
    elif isinstance(widget, forms.Textarea):
        widget.attrs.update({
            "class": AREA,
            "rows": widget.attrs.get("rows", 3),
        })
    else:
        widget.attrs.update({"class": INPUT})

    if isinstance(field, forms.DateField):
        widget.attrs.update({
            "type": "text",
            "placeholder": "dd/mm/yyyy",
            "inputmode": "numeric",
        })


class StyledModelFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            style_widget(field)


class StyledInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)

        labels = FIJIAN_INLINE_LABELS.get(form._meta.model.__name__, {})

        for name, field in form.fields.items():
            field.label = labels.get(name, field.label)
            style_widget(field)


class TNKReportForm(StyledModelFormMixin, forms.ModelForm):
    field_order = ["quarter", "year"]

    class Meta:
        model = TNKReport
        exclude = ["owner", "status", "submitted_at", "created_at", "updated_at"]

        labels = {
            # Tukutuku Raraba
            "quarter": "Ripote ni vula ko",
            "year": "Ena yabaki ko",
            "village": "Yaca ni Koro",
            "district": "Tikina",
            "province": "Yasana",
            "village_headman_name": "Yaca ni Turaga ni Koro",
            "village_headman_age": "Yabaki ni bula nei Turaga ni Koro",
            "appointment_month_year": "Na gauna ka tekivu cakacaka mai kina",

            # Bose kei na Vuvale
            "village_meetings_count": "Wiliwili ni Bose Vakoro ena 3 na Vula sa oji",
            "household_count": "Levu ni Vuvale ena loma ni Koro",
            "bose_vanua_count": "Wiliwili ni Bose Vakavanua",

            # Veivakadodonutaki
            "correction_reintegration_plan": "Tuvatuva ni Veivakadodonutaki",

            # Wai kei na Valelailai
            "water_problem_responsible_agency": "Tabana e Qarava na Leqa ni Wai",
            "water_challenges": "Leqa ni Wai",
            "water_sanitation_challenges": "Bolebole se Dredre ena Maroroi ni Wai kei na Tiko Savasava",
            "toilet_wastewater_agency": "Tabana e Qarava na Valelailai kei na Savasava",
            "toilet_wastewater_challenges": "Leqa ni Vakadrodroi tani ni Wai ni Vale Lailai",

            # IVDP kei na Tuvatuva
            "ivdp_progress_started": "Sa bau tosoi na cakacakataki ni so na IVDP?",
            "ivdp_unfinished_reason": "Na Vuna e Sega ni Vakacavari Kina",

            # Yau Bula kei na Leqa Tubu Koso
            "yaubula_current_plan": "Tuvatuva ni Yau Bula ena Gauna Qo",
            "yaubula_management_plan": "Tuvatuva ni Qaravi Yau Bula",
            "disaster_current_plan": "Tuvatuva ni Leqa Tubu Koso ena Gauna Qo",
            "disaster_future_plan": "Tuvatuva ni Leqa Tubu Koso ena Veigauna Mai Muri",
            "has_evacuation_centre": "E Tiko na Vale ni Dro?",
            "evacuation_centre_capacity": "Lewe vica e rawa ni vakatikori ena loma ni Vale ni Dro",
            "has_male_female_restrooms": "E Tiko na Valelailai ni Tagane kei na Yalewa?",

            # Draki Veisau
            "climate_change_impact": "E tatara tiko ena loma ni Koro na revurevu ni Draki Veisau?",
            "climate_change_impact_details": "Vakamacalataka na Kena i Tukutuku",
            "climate_change_solution_done": "E qaravi beka eso nai tuvatuva me walia na revurevu ni draki veisau ena vula 3 sa oji?",
            "climate_change_solution_details": "Vakamacalataka na Veiqaravi sa Cakavi",

           
        }


class ApprovalActionForm(forms.Form):
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": AREA, "rows": 3}),
        label="Comment",
    )
    acknowledge = forms.BooleanField(
        required=True,
        label="I confirm this digital acknowledgement.",
        widget=forms.CheckboxInput(attrs={"class": CHECKBOX}),
    )


class WasteManagementForm(StyledModelFormMixin, forms.ModelForm):
    class Meta:
        model = WasteManagement
        fields = [
            "village_dump",
            "village_boundary_clean",
            "household_dump",
            "garbage_truck",
        ]

        labels = {
            "village_dump": "E tiko na iSovasova ni benu ni koro?",
            "village_boundary_clean": "Benuci na iBili ni Koro?",
            "household_dump": "E tiko na iSovasova ni benu ni vale yadua?",
            "garbage_truck": "Lori ni Benu?",
        }

class VisitForm(StyledModelFormMixin, forms.ModelForm):
    class Meta:
        model = Visit
        fields = [
            "visit_type",
            "officer_name",
            "visit_date",
            "purpose",
        ]

        labels = {
            "visit_type": "Ko cei e Veisiko",
            "officer_name": "Vakailesilesi e Veisiko",
            "visit_date": "Tiki ni siga ni Veisiko",
            "purpose": "Naki ni Veisiko",
        }


VisitFormSet = inlineformset_factory(
    TNKReport,
    Visit,
    form=VisitForm,
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

class MeetingDecisionForm(StyledModelFormMixin, forms.ModelForm):
    class Meta:
        model = VillageMeetingDecision
        fields = [
            "decision",
            "implemented",
            "reason_not_implemented",
        ]

        labels = {
            "decision": "Lewa ni Bose",
            "implemented": "Sa Vakayacori?",
            "reason_not_implemented": "Kevaka e Sega ni Vakayacori, Na Cava na Vuna?",
        }

MeetingDecisionFormSet = inlineformset_factory(
    TNKReport,
    VillageMeetingDecision,
    form=MeetingDecisionForm,
    extra=0,
    can_delete=False,
    formset=StyledInlineFormSet,
)

class VillageCommitteeForm(StyledModelFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        committee_type = (
            self.data.get(self.add_prefix("committee_type"))
            if self.is_bound
            else self.initial.get("committee_type") or self.instance.committee_type
        )
        self.committee_label = dict(VillageCommittee.COMMITTEE_TYPES).get(
            committee_type,
            "",
        )

    class Meta:
        model = VillageCommittee
        fields = [
            "committee_type",
            "exists",
            "male_members",
            "female_members",
            "meetings_last_3_months",
        ]
        labels = {
            "committee_type": "Mataqali ni Komiti",
            "exists": "E Tiko na Komiti?",
            "male_members": "Lewe ni Tagane",
            "female_members": "Lewe ni Marama",
            "meetings_last_3_months": "Wiliwili ni Bose ena 3 na Vula Sa Oti",
        }
        widgets = {
            "committee_type": forms.HiddenInput(),
        }


CommitteeFormSet = inlineformset_factory(
    TNKReport,
    VillageCommittee,
    form=VillageCommitteeForm,
    extra=len(VillageCommittee.COMMITTEE_TYPES),
    can_delete=False,
    formset=StyledInlineFormSet,
)

LawOffenceFormSet = inlineformset_factory(
    TNKReport,
    LawOffence,
    fields=["offence_name", "count", "reported_to_law", "reason_not_reported"],
    extra=len(LawOffence.OFFENCE_TYPES),
    can_delete=False,
    formset=StyledInlineFormSet,
)

CorrectionReturneeFormSet = inlineformset_factory(
    TNKReport,
    CorrectionReturnee,
    fields=["name", "rehabilitation_done", "current_activity"],
    extra=0,
    can_delete=False,
    formset=StyledInlineFormSet,
)

TrainingFormSet = inlineformset_factory(
    TNKReport,
    Training,
    fields=[
        "training_type",
        "title",
        "organization",
        "date",
        "purpose",
        "participants_count",
        "outcome",
    ],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

PopulationFormSet = inlineformset_factory(
    TNKReport,
    PopulationAgeGroup,
    fields=["gender", "age_group", "count"],
    extra=len(PopulationAgeGroup.GENDER) * len(PopulationAgeGroup.AGE_GROUP),
    can_delete=False,
    formset=StyledInlineFormSet,
)

HousingFormSet = inlineformset_factory(
    TNKReport,
    HousingCount,
    fields=["house_type", "material", "count"],
    extra=len(HousingCount.HOUSE_TYPE) * len(HousingCount.MATERIAL),
    can_delete=False,
    formset=StyledInlineFormSet,
)

WaterSourceFormSet = inlineformset_factory(
    TNKReport,
    WaterSource,
    fields=["source", "selected"],
    extra=len(WaterSource.SOURCE),
    can_delete=False,
    formset=StyledInlineFormSet,
)

WaterCommitteeQuestionFormSet = inlineformset_factory(
    TNKReport,
    WaterCommitteeQuestion,
    fields=["question", "answer"],
    extra=len(WaterCommitteeQuestion.QUESTIONS),
    can_delete=False,
    formset=StyledInlineFormSet,
)

WaterCommitteeMemberFormSet = inlineformset_factory(
    TNKReport,
    WaterCommitteeMember,
    fields=["name"],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

ToiletTypeFormSet = inlineformset_factory(
    TNKReport,
    ToiletType,
    fields=["toilet_type", "count"],
    extra=len(ToiletType.TOILET_TYPE),
    can_delete=False,
    formset=StyledInlineFormSet,
)

ElectricityFormSet = inlineformset_factory(
    TNKReport,
    ElectricitySource,
    fields=["source", "house_count"],
    extra=len(ElectricitySource.SOURCE),
    can_delete=False,
    formset=StyledInlineFormSet,
)

HealthConditionFormSet = inlineformset_factory(
    TNKReport,
    HealthConditionCount,
    fields=["condition_name", "age_group", "count"],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

DisabilityFormSet = inlineformset_factory(
    TNKReport,
    DisabilityCount,
    fields=["disability_name", "age_group", "count"],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

CropFormSet = inlineformset_factory(
    TNKReport,
    CropCount,
    fields=["category", "crop_name", "plantation_count"],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

IVDPProjectFormSet = inlineformset_factory(
    TNKReport,
    IVDPProject,
    fields=[
        "project_name",
        "project_number",
        "priority_area",
        "work_done",
        "application_prepared",
        "funding_agency",
        "materials_received",
        "problem_reason",
        "solution",
    ],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

IVDPScheduleFormSet = inlineformset_factory(
    TNKReport,
    IVDPImplementationSchedule,
    fields=[
        "project",
        "responsibility",
        "organization",
        "start_date",
        "end_date",
        "consultation_approval",
        "commencement",
        "priority_area_achieved_50",
        "project_completion",
    ],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

BusinessFormSet = inlineformset_factory(
    TNKReport,
    Business,
    fields=[
        "business_name",
        "owner_name",
        "licensed",
        "business_type",
        "years_running",
    ],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)


BusinessTrainingFormSet = inlineformset_factory(
    TNKReport,
    BusinessTraining,
    fields=[
        "course_name",
        "organization",
        "date",
        "purpose",
        "participants_count",
        "outcome",
    ],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

AssetSavingFormSet = inlineformset_factory(
    TNKReport,
    VillageAssetSaving,
    fields=["question", "answer", "description"],
    extra=len(VillageAssetSaving.QUESTIONS),
    can_delete=False,
    formset=StyledInlineFormSet,
)

EvacuationMaterialFormSet = inlineformset_factory(
    TNKReport,
    EvacuationCentreMaterial,
    fields=["material", "selected"],
    extra=len(EvacuationCentreMaterial.MATERIAL),
    can_delete=False,
    formset=StyledInlineFormSet,
)

TraditionalTitleFormSet = inlineformset_factory(
    TNKReport,
    TraditionalTitleStatus,
    fields=[
        "title_type",
        "yavusa_mataqali_count",
        "confirmed_count",
        "unconfirmed_count",
        "being_processed",
    ],
    extra=len(TraditionalTitleStatus.TITLE_TYPE),
    can_delete=False,
    formset=StyledInlineFormSet,
)

CulturalKnowledgeFormSet = inlineformset_factory(
    TNKReport,
    CulturalKnowledge,
    fields=["knowledge_type", "preservation_plan"],
    extra=1,
    can_delete=True,
    formset=StyledInlineFormSet,
)

TNK_SECTIONS = (
    (
        "Tukutuku Raraba",
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
    (
        "Levu ni Bose kei na Vuvale",
        (
            "village_meetings_count",
            "household_count",
            "bose_vanua_count",
        ),
    ),
    (
        "Veivakadodonutaki",
        (
            "correction_reintegration_plan",
        ),
    ),
    (
        "Wai kei na Valelailai",
        (
            "water_problem_responsible_agency",
            "water_challenges",
            "water_sanitation_challenges",
            "toilet_wastewater_agency",
            "toilet_wastewater_challenges",
        ),
    ),
    (
        "IVDP kei na Tuvatuva",
        (
            "ivdp_progress_started",
            "ivdp_unfinished_reason",
        ),
    ),
    (
        "Yau Bula kei na Leqa Tubu Koso",
        (
            "yaubula_current_plan",
            "yaubula_management_plan",
            "disaster_current_plan",
            "disaster_future_plan",
            "has_evacuation_centre",
            "evacuation_centre_capacity",
            "has_male_female_restrooms",
        ),
    ),
    (
        "Draki Veisau",
        (
            "climate_change_impact",
            "climate_change_impact_details",
            "climate_change_solution_done",
            "climate_change_solution_details",
        ),
    ),
)


TNK_FORMSET_TITLES = {
    "visits": "Veisiko",
    "decisions": "Lewani ni Bose Vakoro",
    "committees": "Komiti ni Koro",
    "law_offences": "Lawa kei na Veivakacalai",
    "returnees": "Lesu mai na Veivakadodonutaki",
    "trainings": "Vuli",
    "population": "Tagane-Marama",
    "housing": "Vale",
    "water_sources": "Vurevure ni Wai",
    "water_q": "Taro ni Komiti ni Wai",
    "water_members": "Lewe ni Komiti ni Wai",
    "toilets": "Mataqali Valelailai",
    "electricity": "Livaliva",
    "health": "Tiko Bulabula",
    "disabilities": "Vakaleqai ni Yago",
    "crops": "Teitei",
    "ivdp_projects": "IVDP Projects",
    "ivdp_schedule": "Tuvatuva ni IVDP",
    "businesses": "Bisinisi",
    "assets": "Yau kei na Maroroi",
    "evacuation": "Vale ni Dro",
    "titles": "iTutu Vakavanua",
    "culture": "Kilaka Vakavanua",
}
