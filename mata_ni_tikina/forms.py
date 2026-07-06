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
    TikinaEducationTraining,
    TikinaIncomeActivity,
    TikinaSocialIndicator,
    TikinaVillageVisit,
    TreePlantingTraining,
    VagalalaSettlement,
)


MNT_FIJIAN_INLINE_LABELS = {
    "KoroUnderTikina": {"village_name": "Yaca ni Koro", "traditional_leader": "Turaga / iLiuliu Vakavanua", "installed": "Sa Buli oti vakavanua?"},
    "VagalalaSettlement": {"settlement_name": "Yaca ni iTikotiko Vagalala", "household_head": "Liuliu ni Tikotiko", "population_count": "Wiliwili taucoko ni leweni vanua era tiko eke", "family_count": "Wiliwili ni vuvale era tiko eke"},
    "SettlementRegistrationRequest": {"settlement_name": "Yaca ni iTikotiko", "status": "iTuvaki", "notes": "Vakamacala"},
    "TikinaCoordinationStatus": {"entity": "Ko ira na", "status": "iTuvaki ni Veisemati kei na Cakacakavata"},
    "TikinaDispute": {"description": "Veileti se Leqa", "resolution": "Kenai Wali"},
    "TikinaSocialIndicator": {"indicator": "iVakatakilakila", "trend": "iTuvaki"},
    "TikinaEducationTraining": {"training_type": "Mataqali Vuli e vakayacori", "training_leader": "Liutaka na Veituberi", "participants_count": "Wiliwili ni lewe ni Vuli", "benefit": "Kena Yaga ena bula ni lewe ni Vanua"},
    "IncomeSourceItem": {"category": "Mataqali iVurevure ni Lavo cava e tiko ena loma ni Jikina", "ownership_or_detail": "Na kena Taukeni kei na kena i Vakamacala", "count_or_amount": "Wiliwili se kenai Levu ni vurevure ni lavo oqo"},
    "TreePlantingTraining": {"tree_type": "Mataqali Kau", "training_conducted": "Sa Vakayacori na Vuli?", "training_leader": "Tabana kei koya ka vakayaco Vuli", "participants_count": "Wiliwili ni Lewe ni Vuli", "villager_benefit": "Yaga vei ira na lewe ni koro"},
    "TikinaIncomeActivity": {"activity": "Toqa nai vurevure qo ke veisotavi kei na nomu nanuma", "selected": "Toqa"},
    "CouncilSavingsAccount": {"funds_held": "E maroroi Lavo tu na Matabose ni Jikina?", "bank": "Baqe / Soqosoqo"},
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
            "full_name": "Yacamuni Taucoko",
            "age": "Yabaki ni Bula",
            "village": "Nomuni Koro",
            "tikina": "Jikina",
            "province": "Yasana",
            "tikina_population": "Wiliwili ni Lewe ni Tikina (era tiko ena Vanua)",
            "announcements_made_count": "Ai Cavuti raraba",
            "traditional_announcements_received_count": "Vakarorogo vakavanua kivua na",
            "vagalala_population_total": "Wiliwili Taucoko ni lewe ni vanua enai iTikotiko Vagalala",
            "vagalala_family_total": "Wiliwili Taucoko ni Vuvale ena iTikotiko Vagalala",
            "villages_surveyed_count": "Wiliwili ni Koro sa Soveyataki",
            "villages_pending_survey_count": "Wiliwili ni Koro e se bera ni Soveyataki",
            "council_head_name": "Yaca ni Liuliu ni Matabose ni Jikina",
            "council_head_age": "Yabaki ni Liuliu ni Matabose ni Jikina",
            "council_turaga_count": "Wiliwili ni Turaga",
            "council_marama_count": "Wiliwili ni Marama",
            "council_daunivakasala_count": "Wiliwili ni Daunivakasala",
            "council_total_attendees": "Wiliwili Taucoko",
            "council_meeting_frequency": "Gauna e dau vakayacori kina na Bose",
            "council_additional_notes": "Eso tale na ka koni via tukuna me baleta na matabose ni Jikina?",
            "coordination_additional_notes": "Eso tale na ka koni via vakaraitaka me baleta na nodra veisemati ka cakacakavata na veiliutaki?",
            "has_development_plan": "E sa tiko beka nai Tuvatuva raraba ni Veivakatorocaketaki ni Jikina?",
            "education_council_decision": "Lewa ni Matabose me baleta na Vuli ka vakayacori ena vulatolu sa oji",
            "education_next_quarter_decision": "Lewa ni Matabose me baleta na vuli ena Vulatolu mai qo",
            "income_trend": "Soqoni ni veika e rawati enai vurevure ni lavo",
            "income_council_decision": "Lewa ni Matabose me baleta nai vurevure ni lavo ena vulatolu mai oqo",
            "infrastructure_trend": "Tuvaki ni Veivakatorocaketaki ena vula tolu sa oji",
            "villages_with_phone_count": "Koro e tiko kina na Talevoni",
            "villages_with_tv_count": "Koro e tiko kina na TV",
            "boat_count": "Wiliwili ni Waqa",
            "vehicle_count": "Wiliwili ni Lori / Motoka",
            "villages_with_road_access_count": "Koro e tiko kina na Gaunisala",
            "new_roads_built_km": "Kilomita ni Gaunisala Vou",
            "development_council_decision": "Lewa ni Matabose me baleta na Veivakatorocaketaki ena vula tolu mai oqo",
            "govt_financial_assistance_amount": "Veivuke Vakailavo ni Matanitu",
            "govt_assisting_department": "Tabana ni Matanitu e Veivuke",
            "govt_official_visits_count": "Wiliwili ni Veisiko ni Vakailesilesi ni Matanitu",
            "govt_projects_covered": "Tuvatuva ni Matanitu e Qaravi",
            "govt_partnership_notes": "Na veika e via vakaraitaki me baleta na cakacakavata kei na Matanitu",
            "ngo_awareness_programs_notes": "Ulutaga e qaravi ena cakacakavata oqo",
            "ngo_financial_assistance_amount": "Kenai levu vakailavo na cakacakavata se veivuke oqo",
            "ngo_program_name": "Yaca ni Program ka qaravi",
            "ngo_project_equipment_value": "Sau ni ka vakailavo ni yaya era vakayagataki",
            "ngo_project_name": "Yaca ni Project ka vakaiyayataki ena veivuke se cakacakavata oqo",
            "ngo_partnership_notes": "E tiko beka eso na ka ko via vakaraitaka ena cakacakavata se veivuke kei na NGO se Tabana oqo",
            "council_funds_held": "E maroroi Lavo tu na Matabose ni Jikina?",
            "soli_target_amount": "Soli e lavaki ena yabaki qo",
            "soli_contributor_count": "Wiliwili ni Tamata era Soli",
            "soli_collected_amount": "Levu ni Soli ni Yasana sa soli rawa",
            "soli_balance_amount": "Vo ni Lavo me Kumuni",
            "soli_collection_method": "Sala ni Kumuni Soli",
            "fund_growth_notes": "Eso tale beka na ka koni via vakaraitaka me baleta nai tavi oqo",
            "has_registered_farmland": "E tiko na Qele ni Teitei se Leasetaki tiko beka eso ka ra sa register oti?",
            "farmland_lease_count": "Wiliwili ni Lease ni Qele",
            "farmland_acres_leased": "Levu ni Eka(Hectare) ni Qele sa Leasetaki",
            "farmland_lease_years_covered": "Yabaki e Kovuti ena Lease",
            "farmland_development_notes": "Eso tale na ka koni via vakaraitaka me baleta ni qele ni teitei kei koya era lisitaki ena loma ni tikina?",
            "reps_attend_meetings": "Era dau tiko kece na vakailesilesi ena bose?",
            "reps_understand_training_needs": "Matata ka veisotavi kei na ka e gadrevi nodra veivakasalataki?",
            "reps_assist_report_writing": "Era dau veivuke ena veika vakaivola ni veivakatorocaketaki?",
            "reps_help_outside_meetings": "Era dau veitalevi se veiqaravi talega ena taudaku ni gauna ni bose?",
            "reps_additional_notes": "Veika tale eso koni via vakaraitaka me baleji ira nai vakailesilesi ena loma ni Jikina",
            "reps_council_decision": "Lewa ni Matabose",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("tikina_population", "vagalala_population_total", "vagalala_family_total", "council_total_attendees"):
            if name in self.fields:
                self.fields[name].disabled = True
                self.fields[name].required = False
        for name, field in self.fields.items():
            field.help_text = field.help_text or "Sa kerei na kena vakaleweni na tikina qo"


KoroUnderTikinaFormSet = inlineformset_factory(MNTReport, KoroUnderTikina, fields=["village_name", "traditional_leader", "installed"], extra=1, can_delete=False, formset=MNTInlineFormSet)
VagalalaSettlementFormSet = inlineformset_factory(MNTReport, VagalalaSettlement, fields=["settlement_name", "household_head", "population_count", "family_count"], extra=1, can_delete=False, formset=MNTInlineFormSet)
SettlementRegistrationFormSet = inlineformset_factory(MNTReport, SettlementRegistrationRequest, fields=["settlement_name", "status", "notes"], extra=1, can_delete=False, formset=MNTInlineFormSet)
CoordinationStatusFormSet = inlineformset_factory(MNTReport, TikinaCoordinationStatus, fields=["entity", "status"], extra=len(TikinaCoordinationStatus.ENTITY_CHOICES), can_delete=False, formset=MNTInlineFormSet)
DisputeFormSet = inlineformset_factory(MNTReport, TikinaDispute, fields=["description", "resolution"], extra=1, can_delete=False, formset=MNTInlineFormSet)
SocialIndicatorFormSet = inlineformset_factory(MNTReport, TikinaSocialIndicator, fields=["indicator", "trend"], extra=len(TikinaSocialIndicator.INDICATOR_CHOICES), can_delete=False, formset=MNTInlineFormSet)
EducationTrainingFormSet = inlineformset_factory(MNTReport, TikinaEducationTraining, fields=["training_type", "training_leader", "participants_count", "benefit"], extra=1, can_delete=False, formset=MNTInlineFormSet)
IncomeSourceFormSet = inlineformset_factory(MNTReport, IncomeSourceItem, fields=["category", "ownership_or_detail", "count_or_amount"], extra=1, can_delete=False, formset=MNTInlineFormSet)
TreePlantingFormSet = inlineformset_factory(MNTReport, TreePlantingTraining, fields=["tree_type", "training_conducted", "training_leader", "participants_count", "villager_benefit"], extra=1, can_delete=False, formset=MNTInlineFormSet)
IncomeActivityFormSet = inlineformset_factory(MNTReport, TikinaIncomeActivity, fields=["activity", "selected"], extra=len(TikinaIncomeActivity.ACTIVITY_CHOICES), can_delete=False, formset=MNTInlineFormSet)
SavingsAccountFormSet = inlineformset_factory(MNTReport, CouncilSavingsAccount, fields=["funds_held", "bank"], extra=1, can_delete=False, formset=MNTInlineFormSet)
FundChallengeFormSet = inlineformset_factory(MNTReport, FundCollectionChallenge, fields=["challenge", "selected"], extra=len(FundCollectionChallenge.CHALLENGE_CHOICES), can_delete=False, formset=MNTInlineFormSet)
ChallengeIndicatorFormSet = inlineformset_factory(MNTReport, TikinaChallengeIndicator, fields=["indicator", "selected"], extra=len(TikinaChallengeIndicator.INDICATOR_CHOICES), can_delete=False, formset=MNTInlineFormSet)
VillageVisitFormSet = inlineformset_factory(MNTReport, TikinaVillageVisit, fields=["visit_date", "village_name", "role_performed", "turaga_ni_koro_confirmation"], extra=1, can_delete=False, formset=MNTInlineFormSet)
SignatureFormSet = inlineformset_factory(MNTReport, Signature, fields=["role", "name", "signed", "signed_date"], extra=len(Signature.ROLE_CHOICES), can_delete=False, formset=MNTInlineFormSet)


MNT_SECTIONS = (
    ("1.1-1.6 Tukutuku Raraba", ("quarter", "year", "full_name", "age", "village", "tikina", "province", "tikina_population")),
    ("1.8 Ai Cavuti Raraba Vakavanua ni Jikina", ("announcements_made_count", "traditional_announcements_received_count")),
    ("1.9 iTikotiko Vagalala - Wiliwili Taucoko", ("vagalala_population_total", "vagalala_family_total")),
    ("1.10 Soveyataki ni Koro", ("villages_surveyed_count", "villages_pending_survey_count")),
    ("2.0 Matabose ni Tikina", ("council_head_name", "council_head_age", "council_turaga_count", "council_marama_count", "council_daunivakasala_count", "council_total_attendees", "council_meeting_frequency", "council_additional_notes")),
    ("3.0 Sema kei na Cakacakavata", ("coordination_additional_notes",)),
    ("4.1-4.2 Tuvatuva ni Matabose ni Tikina", ("has_development_plan", "education_council_decision", "education_next_quarter_decision", "income_trend", "income_council_decision", "infrastructure_trend", "villages_with_phone_count", "villages_with_tv_count", "boat_count", "vehicle_count", "villages_with_road_access_count", "new_roads_built_km", "development_council_decision")),
    ("4.6 Veitokani kei na Matanitu", ("govt_financial_assistance_amount", "govt_assisting_department", "govt_official_visits_count", "govt_projects_covered", "govt_partnership_notes")),
    ("4.7 Veitokani kei na NGO", ("ngo_awareness_programs_notes", "ngo_financial_assistance_amount", "ngo_program_name", "ngo_project_equipment_value", "ngo_project_name", "ngo_partnership_notes")),
    ("5.3 Soli ni Yasana", ("soli_target_amount", "soli_contributor_count", "soli_collected_amount", "soli_balance_amount", "soli_collection_method")),
    ("5.6 Veika tale eso", ("fund_growth_notes",)),
    ("6.0 Tuvaki ni Qele ni Teitei", ("has_registered_farmland", "farmland_lease_count", "farmland_acres_leased", "farmland_lease_years_covered", "farmland_development_notes")),
    ("7.0 Vakaitavi ni Vakailesilesi", ("reps_attend_meetings", "reps_understand_training_needs", "reps_assist_report_writing", "reps_help_outside_meetings", "reps_additional_notes", "reps_council_decision")),
)


MNT_FORMSET_TITLES = {
    "koro_under_tikina": "1.7 Na Koro ena loma ni Tikina",
    "vagalala_settlements": "1.9 Tikotiko ni Vagalala",
    "settlement_registrations": "1.11 Kerekere ni Registertaki ni iTikotiko Vagalala me Koro",
    "coordination_status": "3.1-3.4 iTuvaki ni Veisemati kei Cakacakavata",
    "disputes": "3.4 Veileti se Leqa e yaco kei na kena i wali",
    "social_indicators": "4.2 Tuvatuva ni Veivakatorocaketaki - na veika sa vakayacori rawa loma ni vulatolu sa oti",
    "education_trainings": "4.2(v) Na Vuli ni Lewenivanua",
    "income_sources": "4.3 iVurevure ni Lavo",
    "tree_planting": "4.4 Vuli ni Tei Kau",
    "income_activities": "5.1 Na cava soti nai vurevure ni Lavo ni Jikina?",
    "savings_accounts": "5.2 Lavo ni Matabose ni Jikina - Baqe / Soqosoqo",
    "fund_challenges": "5.5 Bolebole ni Kumuni Lavo",
    "challenge_indicators": "7.1 iVakatakilakila ni Bolebole",
    "village_visits": "8.0 Veitalevi ena Veikoro",
    "signatures": "9-13 Vakadinadina",
}
