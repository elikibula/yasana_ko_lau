from django import forms
from django.forms import inlineformset_factory

from common.form_mixins import StyledInlineFormSet, StyledModelFormMixin

from .models import (
    CouncilSavingsAccount,
    FundCollectionChallenge,
    IncomeSourceItem,
    KoroUnderTikina,
    MNTReport,
    SettlementRegistrationRequest,
    Signature,
    TikinaChallengeIndicator,
    TikinaCoordinationStatus,
    TikinaDispute,
    TikinaIncomeActivity,
    TikinaSocialIndicator,
    TikinaVillageVisit,
    TreePlantingTraining,
    VagalalaSettlement,
)


MNT_FIJIAN_INLINE_LABELS = {
    "KoroUnderTikina": {"village_name": "Yaca ni Koro", "traditional_leader": "Turaga / iLiuliu Vakavanua"},
    "VagalalaSettlement": {"settlement_name": "Yaca ni iTikotiko Vagalala", "household_head": "Ulunivuvale"},
    "SettlementRegistrationRequest": {"settlement_name": "Yaca ni iTikotiko", "status": "iTuvaki", "notes": "Vakamacala"},
    "TikinaCoordinationStatus": {"entity": "iWasewase", "status": "iTuvaki ni Veisemati"},
    "TikinaDispute": {"description": "Veileti / Leqa", "resolution": "Sala ni Wali"},
    "TikinaSocialIndicator": {"indicator": "iVakatakilakila", "trend": "iTuvaki"},
    "IncomeSourceItem": {"category": "Mataqali iVurevure ni Lavo", "ownership_or_detail": "Taukei / Vakamacala", "count_or_amount": "Wiliwili / Levu"},
    "TreePlantingTraining": {"tree_type": "Mataqali Kau", "training_conducted": "Sa Vakayacori na Vuli?", "training_leader": "Liuliu ni Vuli", "participants_count": "Wiliwili ni Lewe ni Vuli", "villager_benefit": "Yaga vei ira na lewe ni koro"},
    "TikinaIncomeActivity": {"activity": "Cakacaka ni Vakatubuilavo", "selected": "Toqa"},
    "CouncilSavingsAccount": {"bank": "Baqe / Soqosoqo", "saving_level": "iVakatagedegede ni maroroi lavo", "account_number": "Naba ni Akaude", "amount": "Levu ni Lavo"},
    "FundCollectionChallenge": {"challenge": "Bolebole", "selected": "Toqa"},
    "TikinaChallengeIndicator": {"indicator": "iVakatakilakila ni Bolebole", "selected": "Toqa"},
    "TikinaVillageVisit": {"visit_date": "Tiki ni Siga", "village_name": "Koro", "role_performed": "iTavi e Qaravi", "turaga_ni_koro_confirmation": "Vakadeitaki mai vua na Turaga ni Koro"},
    "Signature": {"role": "iTutu", "name": "Yaca", "signed": "Sa Saini", "signed_date": "Tiki ni Siga"},
}


class MNTInlineFormSet(StyledInlineFormSet):
    inline_labels = MNT_FIJIAN_INLINE_LABELS


class MNTReportForm(StyledModelFormMixin, forms.ModelForm):
    class Meta:
        model = MNTReport
        exclude = ["owner", "status", "submitted_at", "created_at", "updated_at"]
        labels = {
            "quarter": "Ripote ni vula ko",
            "year": "Ena yabaki ko",
            "full_name": "Yacamuni",
            "age": "Yabaki ni Bula",
            "village": "Nomuni Koro",
            "tikina": "Tikina",
            "province": "Yasana",
            "tikina_population": "Wiliwili ni Lewe ni Tikina",
            "announcements_made_count": "Wiliwili ni Ai Cavuti sa Vakayacori",
            "traditional_announcements_received_count": "Wiliwili ni Ai Cavuti sa Ciqomi",
            "villages_surveyed_count": "Wiliwili ni Koro sa Sovei",
            "villages_pending_survey_count": "Wiliwili ni Koro e se bera ni Sovei",
            "council_head_name": "Yaca ni Liuliu ni Matabose ni Tikina",
            "council_head_age": "Yabaki ni Liuliu",
            "council_turaga_count": "Wiliwili ni Turaga",
            "council_marama_count": "Wiliwili ni Marama",
            "council_daunivakasala_count": "Wiliwili ni Daunivakasala",
            "council_meeting_frequency": "Gauna ni Bose",
            "council_additional_notes": "iKuri ni Vakamacala ni Matabose",
            "coordination_additional_notes": "iKuri ni Vakamacala ni Veisemati",
            "has_development_plan": "E tiko na Tuvatuva ni Veivakatorocaketaki?",
            "education_council_decision": "Lewaleqa ni Matabose me baleta na Vuli",
            "income_trend": "iTuvaki ni iVurevure ni Lavo",
            "income_council_decision": "Lewaleqa ni Matabose me baleta na Lavo",
            "infrastructure_trend": "iTuvaki ni Veivakatorocaketaki",
            "villages_with_phone_count": "Koro e tiko kina na Talevoni",
            "villages_with_tv_count": "Koro e tiko kina na TV",
            "boat_count": "Wiliwili ni Waqa",
            "vehicle_count": "Wiliwili ni Lori / Motoka",
            "villages_with_road_access_count": "Koro e tiko kina na Gaunisala",
            "new_roads_built_km": "Kilomita ni Gaunisala Vou",
            "development_council_decision": "Lewaleqa ni Matabose me baleta na Veivakatorocaketaki",
            "govt_financial_assistance_amount": "Veivuke Vakailavo ni Matanitu",
            "govt_assisting_department": "Tabana ni Matanitu e Veivuke",
            "govt_official_visits_count": "Wiliwili ni Veisiko ni Vakailesilesi ni Matanitu",
            "govt_projects_covered": "Tuvatuva ni Matanitu e Qaravi",
            "govt_partnership_notes": "Vakamacala ni Veitokani kei na Matanitu",
            "ngo_awareness_programs_notes": "Vuli / Veivakararamataki ni NGO",
            "ngo_financial_assistance_amount": "Veivuke Vakailavo ni NGO",
            "ngo_program_name": "Yaca ni Porokaramu ni NGO",
            "ngo_project_equipment_value": "Levu ni iYaya ni Project ni NGO",
            "ngo_project_name": "Yaca ni Project ni NGO",
            "ngo_partnership_notes": "Vakamacala ni Veitokani kei na NGO",
            "council_funds_held": "E maroroya tiko na Matabose na lavo?",
            "soli_target_amount": "iNaki ni Soli",
            "soli_contributor_count": "Wiliwili era Soli",
            "soli_collected_amount": "Lavo sa Kumuni",
            "soli_balance_amount": "Vo ni Lavo me Kumuni",
            "soli_collection_method": "Sala ni Kumuni Soli",
            "fund_growth_notes": "Vakamacala ni Tubucake ni Lavo",
            "has_registered_farmland": "E tiko na Qele ni Teitei sa Rejisitiri?",
            "farmland_lease_count": "Wiliwili ni Lease ni Qele",
            "farmland_acres_leased": "Eka ni Qele sa Lease",
            "farmland_lease_years_covered": "Yabaki e Kovuti ena Lease",
            "farmland_development_notes": "Vakamacala ni Vakatorocaketaki ni Qele",
            "reps_attend_meetings": "Era dau tiko na vakailesilesi ena bose?",
            "reps_understand_training_needs": "Era kila na gagadre ni vuli?",
            "reps_assist_report_writing": "Era veivuke ena volai ni ripote?",
            "reps_help_outside_meetings": "Era veivuke ena taudaku ni bose?",
            "reps_additional_notes": "iKuri ni vakamacala ni vakailesilesi",
            "reps_council_decision": "Lewaleqa ni Matabose me baleta na vakailesilesi",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.help_text = field.help_text or "Complete this field for the Mata ni Tikina quarterly report."


KoroUnderTikinaFormSet = inlineformset_factory(MNTReport, KoroUnderTikina, fields=["village_name", "traditional_leader"], extra=1, can_delete=True, formset=MNTInlineFormSet)
VagalalaSettlementFormSet = inlineformset_factory(MNTReport, VagalalaSettlement, fields=["settlement_name", "household_head"], extra=1, can_delete=True, formset=MNTInlineFormSet)
SettlementRegistrationFormSet = inlineformset_factory(MNTReport, SettlementRegistrationRequest, fields=["settlement_name", "status", "notes"], extra=1, can_delete=True, formset=MNTInlineFormSet)
CoordinationStatusFormSet = inlineformset_factory(MNTReport, TikinaCoordinationStatus, fields=["entity", "status"], extra=len(TikinaCoordinationStatus.ENTITY_CHOICES), can_delete=False, formset=MNTInlineFormSet)
DisputeFormSet = inlineformset_factory(MNTReport, TikinaDispute, fields=["description", "resolution"], extra=1, can_delete=True, formset=MNTInlineFormSet)
SocialIndicatorFormSet = inlineformset_factory(MNTReport, TikinaSocialIndicator, fields=["indicator", "trend"], extra=len(TikinaSocialIndicator.INDICATOR_CHOICES), can_delete=False, formset=MNTInlineFormSet)
IncomeSourceFormSet = inlineformset_factory(MNTReport, IncomeSourceItem, fields=["category", "ownership_or_detail", "count_or_amount"], extra=1, can_delete=True, formset=MNTInlineFormSet)
TreePlantingFormSet = inlineformset_factory(MNTReport, TreePlantingTraining, fields=["tree_type", "training_conducted", "training_leader", "participants_count", "villager_benefit"], extra=1, can_delete=True, formset=MNTInlineFormSet)
IncomeActivityFormSet = inlineformset_factory(MNTReport, TikinaIncomeActivity, fields=["activity", "selected"], extra=len(TikinaIncomeActivity.ACTIVITY_CHOICES), can_delete=False, formset=MNTInlineFormSet)
SavingsAccountFormSet = inlineformset_factory(MNTReport, CouncilSavingsAccount, fields=["bank", "saving_level", "account_number", "amount"], extra=1, can_delete=True, formset=MNTInlineFormSet)
FundChallengeFormSet = inlineformset_factory(MNTReport, FundCollectionChallenge, fields=["challenge", "selected"], extra=len(FundCollectionChallenge.CHALLENGE_CHOICES), can_delete=False, formset=MNTInlineFormSet)
ChallengeIndicatorFormSet = inlineformset_factory(MNTReport, TikinaChallengeIndicator, fields=["indicator", "selected"], extra=len(TikinaChallengeIndicator.INDICATOR_CHOICES), can_delete=False, formset=MNTInlineFormSet)
VillageVisitFormSet = inlineformset_factory(MNTReport, TikinaVillageVisit, fields=["visit_date", "village_name", "role_performed", "turaga_ni_koro_confirmation"], extra=1, can_delete=True, formset=MNTInlineFormSet)
SignatureFormSet = inlineformset_factory(MNTReport, Signature, fields=["role", "name", "signed", "signed_date"], extra=len(Signature.ROLE_CHOICES), can_delete=False, formset=MNTInlineFormSet)


MNT_SECTIONS = (
    ("1.0 Tukutuku Raraba", ("quarter", "year", "full_name", "age", "village", "tikina", "province", "tikina_population")),
    ("1.8 Ai Cavuti Raraba Vakavanua", ("announcements_made_count", "traditional_announcements_received_count")),
    ("1.10 iTuvaki ni Sovei ni Koro", ("villages_surveyed_count", "villages_pending_survey_count")),
    ("2.0 Matabose ni Tikina", ("council_head_name", "council_head_age", "council_turaga_count", "council_marama_count", "council_daunivakasala_count", "council_meeting_frequency", "council_additional_notes")),
    ("3.0 Sema kei na Cakacakavata", ("coordination_additional_notes",)),
    ("4.0 Tuvatuva ni Matabose ni Tikina", ("has_development_plan", "education_council_decision", "income_trend", "income_council_decision", "infrastructure_trend", "villages_with_phone_count", "villages_with_tv_count", "boat_count", "vehicle_count", "villages_with_road_access_count", "new_roads_built_km", "development_council_decision")),
    ("4.0 Veitokani kei na Matanitu", ("govt_financial_assistance_amount", "govt_assisting_department", "govt_official_visits_count", "govt_projects_covered", "govt_partnership_notes")),
    ("4.0 Veitokani kei na NGO", ("ngo_awareness_programs_notes", "ngo_financial_assistance_amount", "ngo_program_name", "ngo_project_equipment_value", "ngo_project_name", "ngo_partnership_notes")),
    ("5.0 Na Veika Vakailavo", ("council_funds_held", "soli_target_amount", "soli_contributor_count", "soli_collected_amount", "soli_balance_amount", "soli_collection_method", "fund_growth_notes")),
    ("6.0 Tuvaki ni Qele ni Teitei", ("has_registered_farmland", "farmland_lease_count", "farmland_acres_leased", "farmland_lease_years_covered", "farmland_development_notes")),
    ("7.0 Vakaitavi ni Vakailesilesi", ("reps_attend_meetings", "reps_understand_training_needs", "reps_assist_report_writing", "reps_help_outside_meetings", "reps_additional_notes", "reps_council_decision")),
)


MNT_FORMSET_TITLES = {
    "koro_under_tikina": "1.7 Na Koro ena loma ni Tikina",
    "vagalala_settlements": "1.9 iTikotiko Vagalala",
    "settlement_registrations": "1.11 Kerekere ni Rejisitiri ni iTikotiko",
    "coordination_status": "3.1-3.4 iTuvaki ni Veisemati",
    "disputes": "3.4 Veileti",
    "social_indicators": "4.2(a) iVakatakilakila ni Tiko Vinaka",
    "income_sources": "4(c) iVurevure ni Lavo",
    "tree_planting": "4(c)v Vuli ni Tei Kau",
    "income_activities": "5(a) Cakacaka ni Vakatubuilavo",
    "savings_accounts": "5(b) Maroroi Lavo",
    "fund_challenges": "5(e) Bolebole ni Kumuni Lavo",
    "challenge_indicators": "7.0 iVakatakilakila ni Bolebole",
    "village_visits": "8.0 Veitalevi ena Veikoro",
    "signatures": "9-13 Vakadinadina",
}
