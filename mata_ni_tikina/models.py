from django.conf import settings
from django.db import models
from django.utils import timezone

from common.reporting_periods import (
    QUARTER_CHOICES,
    is_report_overdue,
    reporting_due_date,
)


class MNTReport(models.Model):
    YES_NO = (("io", "Io"), ("sega", "Sega"))
    QUARTERS = QUARTER_CHOICES
    TREND_CHOICES = (
        ("tubucake", "Tubucake"),
        ("rawa_vakatikina", "Rawa Vakatikina"),
        ("lutusobu", "Lutu Sobu"),
    )
    STATUS_RATING_CHOICES = (
        ("matata", "Matata/Rokovi"),
        ("buwawa", "Buwawa/Luluqa"),
        ("leqa_levu", "Leqa Vakalevu"),
    )
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED_TO_ROKO = "submitted"
    STATUS_APPROVED_BY_ROKO = "approved_roko"
    STATUS_RETURNED_BY_ROKO = "returned_roko"
    STATUS_REJECTED_BY_ROKO = "rejected_roko"
    STATUS_SUBMITTED = STATUS_SUBMITTED_TO_ROKO
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED_TO_ROKO, "Submitted to Roko Tui"),
        (STATUS_APPROVED_BY_ROKO, "Approved by Roko Tui"),
        (STATUS_RETURNED_BY_ROKO, "Returned by Roko Tui"),
        (STATUS_REJECTED_BY_ROKO, "Rejected by Roko Tui"),
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mnt_reports", null=True, blank=True)
    quarter = models.CharField(max_length=2, choices=QUARTERS)
    year = models.PositiveIntegerField()
    full_name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(null=True, blank=True)
    village = models.CharField(max_length=150)
    tikina = models.CharField(max_length=150)
    province = models.CharField(max_length=150)
    tikina_population = models.PositiveIntegerField(default=0)
    announcements_made_count = models.TextField(blank=True)
    traditional_announcements_received_count = models.TextField(blank=True)
    vagalala_population_total = models.PositiveIntegerField(default=0)
    vagalala_family_total = models.PositiveIntegerField(default=0)
    villages_surveyed_count = models.PositiveIntegerField(default=0)
    villages_pending_survey_count = models.PositiveIntegerField(default=0)
    council_head_name = models.CharField(max_length=150, blank=True)
    council_head_age = models.CharField(max_length=50, null=True, blank=True)
    council_turaga_count = models.PositiveIntegerField(default=0)
    council_marama_count = models.PositiveIntegerField(default=0)
    council_daunivakasala_count = models.PositiveIntegerField(default=0)
    council_total_attendees = models.PositiveIntegerField(default=0)
    council_meeting_frequency = models.CharField(max_length=150, blank=True)
    council_additional_notes = models.TextField(blank=True)
    coordination_additional_notes = models.TextField(blank=True)
    has_development_plan = models.CharField(max_length=10, choices=YES_NO, blank=True)
    education_council_decision = models.TextField(blank=True)
    education_next_quarter_decision = models.TextField(blank=True)
    income_trend = models.CharField(max_length=20, choices=TREND_CHOICES, blank=True)
    income_council_decision = models.TextField(blank=True)
    infrastructure_trend = models.CharField(max_length=20, choices=TREND_CHOICES, blank=True)
    villages_with_phone_count = models.PositiveIntegerField(default=0)
    villages_with_tv_count = models.PositiveIntegerField(default=0)
    boat_count = models.PositiveIntegerField(default=0)
    vehicle_count = models.PositiveIntegerField(default=0)
    villages_with_road_access_count = models.PositiveIntegerField(default=0)
    new_roads_built_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    development_council_decision = models.TextField(blank=True)
    govt_financial_assistance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    govt_assisting_department = models.CharField(max_length=200, blank=True)
    govt_official_visits_count = models.PositiveIntegerField(default=0)
    govt_projects_covered = models.TextField(blank=True)
    govt_partnership_notes = models.TextField(blank=True)
    ngo_awareness_programs_notes = models.TextField(blank=True)
    ngo_financial_assistance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ngo_program_name = models.CharField(max_length=200, blank=True)
    ngo_project_equipment_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ngo_project_name = models.CharField(max_length=200, blank=True)
    ngo_partnership_notes = models.TextField(blank=True)
    council_funds_held = models.CharField(max_length=10, choices=YES_NO, blank=True)
    soli_target_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    soli_contributor_count = models.PositiveIntegerField(default=0)
    soli_collected_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    soli_balance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    soli_collection_method = models.TextField(blank=True)
    fund_growth_notes = models.TextField(blank=True)
    has_registered_farmland = models.CharField(max_length=10, choices=YES_NO, blank=True)
    farmland_lease_count = models.PositiveIntegerField(default=0)
    farmland_acres_leased = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    farmland_lease_years_covered = models.CharField(max_length=150, blank=True)
    farmland_development_notes = models.TextField(blank=True)
    reps_attend_meetings = models.CharField(max_length=10, choices=YES_NO, blank=True)
    reps_understand_training_needs = models.CharField(max_length=10, choices=YES_NO, blank=True)
    reps_assist_report_writing = models.CharField(max_length=10, choices=YES_NO, blank=True)
    reps_help_outside_meetings = models.CharField(max_length=10, choices=YES_NO, blank=True)
    reps_additional_notes = models.TextField(blank=True)
    reps_council_decision = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-created_at"]
        constraints = [models.UniqueConstraint(fields=["owner", "quarter", "year"], name="one_mnt_report_per_owner_quarter")]

    def submit(self):
        self.status = self.STATUS_SUBMITTED_TO_ROKO
        if not self.submitted_at:
            self.submitted_at = timezone.now()

    @property
    def due_date(self):
        return reporting_due_date(self.quarter, self.year)

    @property
    def is_overdue(self):
        return is_report_overdue(self)

    def total_villages_under_buli(self):
        return self.koro_under_tikina.filter(installed="io").count()

    def total_disputes(self):
        return self.disputes.count()

    def __str__(self):
        return f"{self.tikina} - {self.quarter} {self.year}"


class MNTApprovalAction(models.Model):
    ACTION_SUBMIT = "submit"
    ACTION_APPROVE = "approve"
    ACTION_RETURN = "return"
    ACTION_REJECT = "reject"
    ACTION_COMMENT = "comment"
    ACTION_CHOICES = (
        (ACTION_SUBMIT, "Submit"),
        (ACTION_APPROVE, "Approve"),
        (ACTION_RETURN, "Return"),
        (ACTION_REJECT, "Reject"),
        (ACTION_COMMENT, "Comment"),
    )

    report = models.ForeignKey(MNTReport, on_delete=models.PROTECT, related_name="approval_actions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mnt_approval_actions")
    user_full_name = models.CharField(max_length=150)
    user_role = models.CharField(max_length=100)
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES)
    from_status = models.CharField(max_length=40, blank=True)
    to_status = models.CharField(max_length=40, blank=True)
    comment = models.TextField(blank=True)
    digital_acknowledgement = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]
        verbose_name = "Mata ni Tikina Approval Action"
        verbose_name_plural = "Mata ni Tikina Approval Actions"

    def __str__(self):
        return f"{self.report} - {self.get_action_type_display()} by {self.user_full_name}"


class KoroUnderTikina(models.Model):
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="koro_under_tikina")
    village_name = models.CharField(max_length=150)
    traditional_leader = models.CharField(max_length=150, blank=True)
    installed = models.CharField(max_length=10, choices=MNTReport.YES_NO, blank=True)


class VagalalaSettlement(models.Model):
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="vagalala_settlements")
    settlement_name = models.CharField(max_length=150)
    household_head = models.CharField(max_length=150, blank=True)
    population_count = models.PositiveIntegerField(default=0)
    family_count = models.PositiveIntegerField(default=0)


class SettlementRegistrationRequest(models.Model):
    STATUS_CHOICES = (("pending", "Pending"), ("registered", "Registered"))
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="settlement_registrations")
    settlement_name = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)


class TikinaCoordinationStatus(models.Model):
    ENTITY_CHOICES = (
        ("yavusa_leadership", "Liuliu ni Yavusa"),
        ("mataqali_leadership", "Liuliu ni Mataqali"),
        ("church_leadership", "Liuliu ni Veimata Lotu"),
        ("organization_leadership", "Liuliu ni Veimata Soqosoqo"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="coordination_statuses")
    entity = models.CharField(max_length=50, choices=ENTITY_CHOICES)
    status = models.CharField(max_length=20, choices=MNTReport.STATUS_RATING_CHOICES, blank=True)


class TikinaDispute(models.Model):
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="disputes")
    description = models.TextField()
    resolution = models.TextField(blank=True)


class TikinaSocialIndicator(models.Model):
    INDICATOR_CHOICES = (
        ("spiritual_life", "Bula Vakayalo"),
        ("traditional_custom", "Tovo Vakavanua"),
        ("drinking_water", "Wai ni gunu"),
        ("food_supply", "Kakana"),
        ("child_welfare_support", "Vukei na Yada kei na Gone luveniyali"),
        ("education", "Na Vuli"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="social_indicators")
    indicator = models.CharField(max_length=50, choices=INDICATOR_CHOICES)
    trend = models.CharField(max_length=20, choices=MNTReport.TREND_CHOICES, blank=True)


class TikinaEducationTraining(models.Model):
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="education_trainings")
    training_type = models.CharField(max_length=200)
    training_leader = models.CharField(max_length=150, blank=True)
    participants_count = models.PositiveIntegerField(default=0)
    benefit = models.TextField(blank=True)


class IncomeSourceItem(models.Model):
    CATEGORY_CHOICES = (
        ("business", "Cicivaki Bisinisi"),
        ("farming", "Commercial Farm"),
        ("fishing", "Commercial Fishing"),
        ("forest_land_use", "Forestry and other Land Use"),
        ("handicrafts", "Bisinisi ni Handicrafts"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="income_sources")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    ownership_or_detail = models.CharField(max_length=200, blank=True)
    count_or_amount = models.PositiveIntegerField(default=0)


class TreePlantingTraining(models.Model):
    TREE_TYPE_CHOICES = (("pine_mahogany", "Pine/Mahogany"), ("traditional", "Traditional"))
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="tree_planting_trainings")
    tree_type = models.CharField(max_length=30, choices=TREE_TYPE_CHOICES)
    training_conducted = models.CharField(max_length=10, choices=MNTReport.YES_NO, blank=True)
    training_leader = models.CharField(max_length=150, blank=True)
    participants_count = models.PositiveIntegerField(default=0)
    villager_benefit = models.TextField(blank=True)


class TikinaIncomeActivity(models.Model):
    ACTIVITY_CHOICES = (
        ("tei_dovu_suka", "Tei Dovu & Suka"),
        ("koula_volitaki", "Koula Volitaki"),
        ("niu_volitaki", "Niu Volitaki"),
        ("tolo_kau_maroroi", "Volitaki ni Tolo ni Kau Maroroi"),
        ("qoli_volitaki_ika", "Na Qoli & Volitaki Ika"),
        ("saravanua", "Cakacaka ni Saravanua"),
        ("yaqona", "Volitaki Yaqona"),
        ("dalo", "Volitaki Dalo"),
        ("kakana_draudrau", "Volitaki Kakana Draudrau"),
        ("sasalu_waitui", "Volitaki ni Sasalu/Waitui"),
        ("susu_manumanu", "Susu Manumanu"),
        ("konitaraki", "Cakacaka Konitaraki"),
        ("liga_buliyaya", "Cakacaka ni Liga/Buliyaya"),
        ("lavo_bonisi", "Vakatubu i Lavo Bonisi"),
        ("vavalagi", "Cakacaka mai Vavalagi"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="income_activities")
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    selected = models.BooleanField(default=False)


class CouncilSavingsAccount(models.Model):
    BANK_CHOICES = (
        ("anz", "ANZ"),
        ("westpac", "Westpac"),
        ("colonial", "Colonial"),
        ("fijian_holdings", "Fijian Holdings"),
        ("unit_trust_fiji", "Unit Trust of Fiji"),
    )
    SAVING_LEVEL_CHOICES = (
        ("vakavuvale", "Vakavuvale"),
        ("vakaitokatoka", "Vakaitokatoka"),
        ("vakamataqali", "Vakamataqali"),
        ("vakoro", "Vakoro"),
        ("vaka_tamata_yadua", "Vaka Tamata Yadua"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="savings_accounts")
    funds_held = models.CharField(max_length=10, choices=MNTReport.YES_NO, blank=True)
    bank = models.CharField(max_length=50, choices=BANK_CHOICES)
    saving_level = models.CharField(max_length=50, choices=SAVING_LEVEL_CHOICES)
    account_number = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


class FundCollectionChallenge(models.Model):
    CHALLENGE_CHOICES = (
        ("road_access", "Dredre na gaunisala"),
        ("no_market", "Sega na makete ni volivolitaki"),
        ("no_boat_or_lorry", "Sega se Dredre na waqa se lori"),
        ("low_produce_price", "Sau ca nai voli"),
        ("low_value_goods", "Lailai nai yau ni veivoli"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="fund_challenges")
    challenge = models.CharField(max_length=50, choices=CHALLENGE_CHOICES)
    selected = models.BooleanField(default=False)


class TikinaChallengeIndicator(models.Model):
    INDICATOR_CHOICES = (
        ("solesolevaki", "Solesolevaki"),
        ("makete", "Vakavinakataki na Makete"),
        ("gaunisala", "Vakavinakataki na Gaunisala"),
        ("waqa", "Vakavinakataki na Waqa"),
        ("vodovodo", "Veivuke ni Vodovodo"),
        ("qele_bulabula", "Veirauti Vinaka/Qele Bulabula"),
        ("takiveiyaga", "Takiveiyaga"),
        ("mamaca", "Rui Mamaca/Dravuisiga"),
        ("suasua", "Rui Levu na Suasua"),
        ("qele_matemate", "Qele Matemate"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="challenge_indicators")
    indicator = models.CharField(max_length=50, choices=INDICATOR_CHOICES)
    selected = models.BooleanField(default=False)


class TikinaVillageVisit(models.Model):
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="village_visits")
    visit_date = models.DateField(null=True, blank=True)
    village_name = models.CharField(max_length=150)
    role_performed = models.TextField(blank=True)
    turaga_ni_koro_confirmation = models.CharField(max_length=150, blank=True)


class Signature(models.Model):
    ROLE_CHOICES = (
        ("mata_ni_tikina", "Mata ni Tikina"),
        ("liuliu_ni_matabose", "Liuliu ni Matabose"),
        ("roko_veivuke", "Roko Veivuke"),
        ("roko_tui", "Roko Tui"),
        ("dauniyau_ni_yasana", "Dauniyau ni Yasana"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="signatures")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    name = models.CharField(max_length=150, blank=True)
    signed = models.BooleanField(default=False)
    signed_date = models.DateField(null=True, blank=True)
