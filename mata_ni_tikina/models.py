from django.conf import settings
from django.db import models
from django.utils import timezone


class MNTReport(models.Model):
    YES_NO = (("io", "Io"), ("sega", "Sega"))
    QUARTERS = (
        ("Q1", "Q1 - January to March"),
        ("Q2", "Q2 - April to June"),
        ("Q3", "Q3 - July to September"),
        ("Q4", "Q4 - October to December"),
    )
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
    STATUS_SUBMITTED = "submitted"
    STATUS_CHOICES = ((STATUS_DRAFT, "Draft"), (STATUS_SUBMITTED, "Submitted"))

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mnt_reports", null=True, blank=True)
    quarter = models.CharField(max_length=2, choices=QUARTERS)
    year = models.PositiveIntegerField()
    full_name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(null=True, blank=True)
    village = models.CharField(max_length=150)
    tikina = models.CharField(max_length=150)
    province = models.CharField(max_length=150)
    tikina_population = models.PositiveIntegerField(default=0)
    announcements_made_count = models.PositiveIntegerField(default=0)
    traditional_announcements_received_count = models.PositiveIntegerField(default=0)
    villages_surveyed_count = models.PositiveIntegerField(default=0)
    villages_pending_survey_count = models.PositiveIntegerField(default=0)
    council_head_name = models.CharField(max_length=150)
    council_head_age = models.PositiveIntegerField(null=True, blank=True)
    council_turaga_count = models.PositiveIntegerField(default=0)
    council_marama_count = models.PositiveIntegerField(default=0)
    council_daunivakasala_count = models.PositiveIntegerField(default=0)
    council_meeting_frequency = models.CharField(max_length=150, blank=True)
    council_additional_notes = models.TextField(blank=True)
    coordination_additional_notes = models.TextField(blank=True)
    has_development_plan = models.CharField(max_length=10, choices=YES_NO, blank=True)
    education_council_decision = models.TextField(blank=True)
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
        self.status = self.STATUS_SUBMITTED
        if not self.submitted_at:
            self.submitted_at = timezone.now()

    def total_villages_under_buli(self):
        return self.koro_under_tikina.count()

    def total_disputes(self):
        return self.disputes.count()

    def __str__(self):
        return f"{self.tikina} - {self.quarter} {self.year}"


class KoroUnderTikina(models.Model):
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="koro_under_tikina")
    village_name = models.CharField(max_length=150)
    traditional_leader = models.CharField(max_length=150, blank=True)


class VagalalaSettlement(models.Model):
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="vagalala_settlements")
    settlement_name = models.CharField(max_length=150)
    household_head = models.CharField(max_length=150, blank=True)


class SettlementRegistrationRequest(models.Model):
    STATUS_CHOICES = (("pending", "Pending"), ("registered", "Registered"))
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="settlement_registrations")
    settlement_name = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)


class TikinaCoordinationStatus(models.Model):
    ENTITY_CHOICES = (
        ("yavusa_leadership", "Yavusa Leadership"),
        ("mataqali_leadership", "Mataqali Leadership"),
        ("church_leadership", "Church Leadership"),
        ("organization_leadership", "Organization Leadership"),
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
        ("spiritual_life", "Spiritual Life"),
        ("traditional_custom", "Traditional Custom"),
        ("drinking_water", "Drinking Water"),
        ("food_supply", "Food Supply"),
        ("child_welfare_support", "Child Welfare Support"),
        ("education", "Education"),
    )
    report = models.ForeignKey(MNTReport, on_delete=models.CASCADE, related_name="social_indicators")
    indicator = models.CharField(max_length=50, choices=INDICATOR_CHOICES)
    trend = models.CharField(max_length=20, choices=MNTReport.TREND_CHOICES, blank=True)


class IncomeSourceItem(models.Model):
    CATEGORY_CHOICES = (
        ("business", "Business"),
        ("farming", "Farming"),
        ("fishing", "Fishing"),
        ("forest_land_use", "Forest/Land Use"),
        ("handicrafts", "Handicrafts"),
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
    bank = models.CharField(max_length=50, choices=BANK_CHOICES)
    saving_level = models.CharField(max_length=50, choices=SAVING_LEVEL_CHOICES)
    account_number = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


class FundCollectionChallenge(models.Model):
    CHALLENGE_CHOICES = (
        ("road_access", "Road Access"),
        ("no_market", "No Market"),
        ("no_boat_or_lorry", "No Boat/Lorry"),
        ("low_produce_price", "Low Produce Price"),
        ("low_value_goods", "Low Value Goods"),
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
