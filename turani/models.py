from django.db import models
from django.conf import settings
from django.utils import timezone


class TNKReport(models.Model):
    YES_NO = (
        ("io", "Io"),
        ("sega", "Sega"),
    )

    QUARTERS = (
        ("Q1", "Q1 - January to March"),
        ("Q2", "Q2 - April to June"),
        ("Q3", "Q3 - July to September"),
        ("Q4", "Q4 - October to December"),
    )

    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tnk_reports",
        null=True,
        blank=True,
    )
    quarter = models.CharField(max_length=2, choices=QUARTERS)
    year = models.PositiveIntegerField()
    village = models.CharField(max_length=150)
    district = models.CharField(max_length=150)
    province = models.CharField(max_length=150)

    village_headman_name = models.CharField(max_length=150)
    village_headman_age = models.PositiveIntegerField(null=True, blank=True)
    appointment_month_year = models.CharField(max_length=100, blank=True)

    village_meetings_count = models.PositiveIntegerField(default=0)
    household_count = models.PositiveIntegerField(default=0)

    correction_reintegration_plan = models.TextField(blank=True)

    water_problem_responsible_agency = models.TextField(blank=True)
    water_challenges = models.TextField(blank=True)
    water_sanitation_challenges = models.TextField(blank=True)
    toilet_wastewater_agency = models.TextField(blank=True)
    toilet_wastewater_challenges = models.TextField(blank=True)

    ivdp_progress_started = models.CharField(
        max_length=10, choices=YES_NO, blank=True
    )
    ivdp_unfinished_reason = models.TextField(blank=True)

    yaubula_current_plan = models.TextField(blank=True)
    yaubula_management_plan = models.TextField(blank=True)

    disaster_current_plan = models.TextField(blank=True)
    disaster_future_plan = models.TextField(blank=True)
    has_evacuation_centre = models.CharField(
        max_length=10, choices=YES_NO, blank=True
    )
    evacuation_centre_capacity = models.PositiveIntegerField(null=True, blank=True)
    has_male_female_restrooms = models.CharField(
        max_length=10, choices=YES_NO, blank=True
    )

    climate_change_impact = models.CharField(
        max_length=10, choices=YES_NO, blank=True
    )
    climate_change_impact_details = models.TextField(blank=True)
    climate_change_solution_done = models.CharField(
        max_length=10, choices=YES_NO, blank=True
    )
    climate_change_solution_details = models.TextField(blank=True)

    bose_vanua_count = models.PositiveIntegerField(default=0)
    roko_veivuke_comment = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def submit(self):
        self.status = self.STATUS_SUBMITTED
        self.submitted_at = timezone.now()

    def total_population(self):
        return sum(item.count for item in self.population.all())

    def total_health_cases(self):
        return sum(item.count for item in self.health_conditions.all())

    def total_offences(self):
        return sum(item.count for item in self.law_offences.all())

    def total_businesses(self):
        return self.businesses.count()

    def total_ivdp_projects(self):
        return self.ivdp_projects.count()

    class Meta:
        ordering = ["-year", "-created_at"]
        verbose_name = "TNK Report"
        verbose_name_plural = "TNK Reports"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "quarter", "year"],
                name="one_tnk_report_per_owner_quarter",
            )
        ]

    def __str__(self):
        return f"{self.village} - {self.quarter} {self.year}"


class Visit(models.Model):
    VISIT_TYPE = (
        ("yasana", "Valevolavola ni Yasana"),
        ("government", "Matanitu  se Taudaku ni Matanitu"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="visits"
    )
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPE)
    officer_name = models.CharField(max_length=150)
    visit_date = models.DateField(null=True, blank=True)
    purpose = models.TextField(blank=True)

    def __str__(self):
        return f"{self.officer_name} - {self.get_visit_type_display()}"


class VillageMeetingDecision(models.Model):
    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="meeting_decisions"
    )
    decision = models.TextField()
    implemented = models.CharField(max_length=10, choices=TNKReport.YES_NO)
    reason_not_implemented = models.TextField(blank=True)

    def __str__(self):
        return self.decision[:80]


class VillageCommittee(models.Model):
    COMMITTEE_TYPES = (
        ("development", "Veivakatorocaketaki"),
        ("health", "Tiko Bulabula"),
        ("water", "Wai"),
        ("yaubula_disaster", "Yau Bula/Leqa Tubu Koso"),
        ("education", "Vuli"),
        ("youth", "Tabagone"),
        ("women", "Marama"),
        ("law", "Lawa"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="committees"
    )
    committee_type = models.CharField(max_length=50, choices=COMMITTEE_TYPES)
    exists = models.CharField(max_length=10, choices=TNKReport.YES_NO)
    male_members = models.PositiveIntegerField(default=0)
    female_members = models.PositiveIntegerField(default=0)
    meetings_last_3_months = models.PositiveIntegerField(default=0)

    def total_members(self):
        return self.male_members + self.female_members

    def __str__(self):
        return self.get_committee_type_display()


class LawOffence(models.Model):
    OFFENCE_TYPES = (
        ("kucu", "Kucu"),
        ("butako", "Butako ena vakarau kaukauwa"),
        ("basu_vale", "Basu vale ni tiko na kena i taukei"),
        ("laba", "Laba"),
        ("veivakamavoataki", "Veivakamavoataki"),
        ("matenikavakasausa", "Matenikavakasausa"),
        ("wai_veivakamatenitaki", "Volitaki ni wai ni veivakamatenitaki"),
        ("violence", "Veivakadolomataki vei ira na Marama/Gone"),
        ("marijuana", "Vakayagataki ni Wainimate ni Veivakamatenitaki (Marijuana)"),
        ("drugs", "Vakayagataki ni Waigaga ni Veivakamatenitaki"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="law_offences"
    )
    offence_name = models.CharField(max_length=255)
    count = models.PositiveIntegerField(default=0)
    reported_to_law = models.CharField(
        max_length=10, choices=TNKReport.YES_NO, blank=True
    )
    reason_not_reported = models.TextField(blank=True)

    def __str__(self):
        return self.offence_name


class CorrectionReturnee(models.Model):
    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="correction_returnees"
    )
    name = models.CharField(max_length=150)
    rehabilitation_done = models.TextField(blank=True)
    current_activity = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Training(models.Model):
    TRAINING_TYPE = (
        ("general", "Vuli/Veivakararamataki"),
        ("business", "Vuli ni Bisinisi"),
        ("vanua", "Vuli ni Matabose ni Veika Vakaitaukei"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="trainings"
    )
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPE)
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    date = models.DateField(null=True, blank=True)
    purpose = models.TextField(blank=True)
    participants_count = models.PositiveIntegerField(default=0)
    outcome = models.TextField(blank=True)

    def __str__(self):
        return self.title


class PopulationAgeGroup(models.Model):
    GENDER = (
        ("yalewa", "Yalewa"),
        ("tagane", "Tagane"),
    )

    AGE_GROUP = (
        ("0_10", "0-10"),
        ("11_20", "11-20"),
        ("21_30", "21-30"),
        ("31_40", "31-40"),
        ("41_50", "41-50"),
        ("51_60", "51-60"),
        ("61_plus", "61+"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="population"
    )
    gender = models.CharField(max_length=20, choices=GENDER)
    age_group = models.CharField(max_length=20, choices=AGE_GROUP)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.get_gender_display()} - {self.get_age_group_display()}"


class HousingCount(models.Model):
    HOUSE_TYPE = (
        ("house", "Vale"),
        ("kitchen", "Vale ni Kuro"),
        ("bathroom", "Vale ni Sili"),
        ("toilet", "Vale Lailai"),
    )

    MATERIAL = (
        ("simede", "Simede"),
        ("kau", "Kau"),
        ("kava", "Kava"),
        ("vakaviti", "Vakaviti"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="housing_counts"
    )
    house_type = models.CharField(max_length=30, choices=HOUSE_TYPE)
    material = models.CharField(max_length=30, choices=MATERIAL)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.get_house_type_display()} - {self.get_material_display()}"


class WaterSource(models.Model):
    SOURCE = (
        ("uciwai", "Uciwai"),
        ("waivure", "Waivure"),
        ("wai_ni_uca", "Wai ni Uca"),
        ("toevu", "Toevu"),
        ("taqe_ni_wai", "Taqe ni Wai"),
        ("waf", "WAF"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="water_sources"
    )
    source = models.CharField(max_length=30, choices=SOURCE)
    selected = models.BooleanField(default=False)

    def __str__(self):
        return self.get_source_display()


class WaterCommitteeQuestion(models.Model):
    QUESTIONS = (
        ("committee_exists", "E tiko beka e dua na Komiti ni Wai ni Koro?"),
        ("meets_regularly", "E ratou dau sota vakawasoma?"),
        ("cleans_sources", "E ratou dau vakasavasavataka nai vakaso ni wai kei na taqe ni wai?"),
        ("log_book", "E tiko beka e dua nai vola (Log Book) me volai kina nai tukutuku ni veika e ratou sa qarava na Komiti?"),
        ("repairs_pipes", "E ratou dau vakavinakataka na leqa ni tolo ni paipo ena gauna e yaco kina?"),
        ("knows_roles", "E ratou kila vakavinaka na Komiti na nodra itavi ena loma ni Koro?"),
    )

    report = models.ForeignKey(
        TNKReport,
        on_delete=models.CASCADE,
        related_name="water_committee_answers",
    )
    question = models.CharField(max_length=255)
    answer = models.BooleanField(default=False)

    def __str__(self):
        return self.question


class WaterCommitteeMember(models.Model):
    report = models.ForeignKey(
        TNKReport,
        on_delete=models.CASCADE,
        related_name="water_committee_members",
    )
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class WasteManagement(models.Model):
    report = models.OneToOneField(
        TNKReport, on_delete=models.CASCADE, related_name="waste_management"
    )
    village_dump = models.CharField(
        max_length=10, choices=TNKReport.YES_NO, blank=True
    )
    village_boundary_clean = models.CharField(
        max_length=10, choices=TNKReport.YES_NO, blank=True
    )
    household_dump = models.CharField(
        max_length=10, choices=TNKReport.YES_NO, blank=True
    )
    garbage_truck = models.CharField(
        max_length=10, choices=TNKReport.YES_NO, blank=True
    )

    def __str__(self):
        return f"Waste Management - {self.report.village}"


class ToiletType(models.Model):
    TOILET_TYPE = (
        ("sovawai", "Sovawai"),
        ("keli", "Keli"),
        ("sewer_line", "Dre - Sewer Line"),
        ("septic_simede", "Dre - Septic Tank Simede"),
        ("septic_dramu", "Dre - Septic Tank Dramu"),
        ("compost", "Compost"),
        ("none", "Sega na Valelailai"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="toilet_types"
    )
    toilet_type = models.CharField(max_length=40, choices=TOILET_TYPE)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.get_toilet_type_display()


class ElectricitySource(models.Model):
    SOURCE = (
        ("fea", "FEA"),
        ("village_generator", "Idini ni Koro"),
        ("windmill", "Windmill"),
        ("private_generator", "Idini Vakaitaukei"),
        ("kerosene", "Karasini/Tabucagi"),
        ("benzene", "Benisini"),
        ("solar", "Solar Energy"),
        ("hydro", "Hydro"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="electricity_sources"
    )
    source = models.CharField(max_length=50, choices=SOURCE)
    house_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.get_source_display()


class HealthConditionCount(models.Model):
    AGE_GROUP = (
        ("0_14", "Gone lalai 0-14"),
        ("15_35", "Tabagone 15-35"),
        ("36_60", "Uabula 36-60"),
        ("60_plus", "Qase 60+"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="health_conditions"
    )
    condition_name = models.CharField(max_length=200)
    age_group = models.CharField(max_length=20, choices=AGE_GROUP)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.condition_name} - {self.get_age_group_display()}"


class DisabilityCount(models.Model):
    AGE_GROUP = HealthConditionCount.AGE_GROUP

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="disabilities"
    )
    disability_name = models.CharField(max_length=200)
    age_group = models.CharField(max_length=20, choices=AGE_GROUP)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.disability_name} - {self.get_age_group_display()}"


class CropCount(models.Model):
    CROP_CATEGORY = (
        ("kakana_draudrau", "Kakana Draudrau"),
        ("kakana_dina", "Kakana Dina"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="crops"
    )
    category = models.CharField(max_length=30, choices=CROP_CATEGORY)
    crop_name = models.CharField(max_length=100)
    plantation_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.crop_name} - {self.get_category_display()}"


class IVDPProject(models.Model):
    PRIORITY_AREA = (
        (1, "Veiliutaki Vinaka"),
        (2, "Tiko Vinaka"),
        (3, "Rawa Ka Vakaiyau"),
        (4, "Maroroi Ni Yau Bula"),
        (5, "Veiliutaki Vinaka Ni Vanua"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="ivdp_projects"
    )
    project_name = models.CharField(max_length=200)
    project_number = models.PositiveIntegerField(null=True, blank=True)
    priority_area = models.PositiveSmallIntegerField(choices=PRIORITY_AREA)
    work_done = models.TextField(blank=True)
    application_prepared = models.CharField(
        max_length=10, choices=TNKReport.YES_NO, blank=True
    )
    funding_agency = models.CharField(max_length=200, blank=True)
    materials_received = models.CharField(
        max_length=10, choices=TNKReport.YES_NO, blank=True
    )
    problem_reason = models.TextField(blank=True)
    solution = models.TextField(blank=True)

    def __str__(self):
        return self.project_name


class Business(models.Model):
    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="businesses"
    )
    business_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=150)
    licensed = models.CharField(max_length=10, choices=TNKReport.YES_NO, blank=True)
    business_type = models.CharField(max_length=200, blank=True)
    years_running = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.business_name


class BusinessTraining(models.Model):
    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="business_trainings"
    )
    course_name = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    date = models.DateField(null=True, blank=True)
    purpose = models.TextField(blank=True)
    participants_count = models.PositiveIntegerField(default=0)
    outcome = models.TextField(blank=True)

    def __str__(self):
        return self.course_name


class VillageAssetSaving(models.Model):
    QUESTIONS = (
        (
            "assets",
            "E tiko beka e so nai Yau Tudei ni Koro? (Lori, Waqa, Vale, Qele, Idini Livaliva, So Tale)",
        ),
        ("investment", "E vakatubui lavo tiko na koro? (Investment)"),
        ("savings", "E maroroi lavo tu na koro? (Baqe/Stock Exchange)"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="assets_savings"
    )
    question = models.CharField(max_length=255)
    answer = models.CharField(max_length=10, choices=TNKReport.YES_NO)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.question


class EvacuationCentreMaterial(models.Model):
    MATERIAL = (
        ("simede", "Simede"),
        ("kau", "Kau"),
        ("kava", "Kava"),
        ("vakaviti", "Vakaviti"),
    )

    report = models.ForeignKey(
        TNKReport,
        on_delete=models.CASCADE,
        related_name="evacuation_centre_materials",
    )
    material = models.CharField(max_length=30, choices=MATERIAL)
    selected = models.BooleanField(default=False)

    def __str__(self):
        return self.get_material_display()


class TraditionalTitleStatus(models.Model):
    TITLE_TYPE = (
        ("turaga_ni_yavusa", "Turaga ni Yavusa"),
        ("turaga_ni_mataqali", "Turaga ni Mataqali"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="traditional_titles"
    )
    title_type = models.CharField(max_length=50, choices=TITLE_TYPE)
    yavusa_mataqali_count = models.PositiveIntegerField(default=0)
    confirmed_count = models.PositiveIntegerField(default=0)
    unconfirmed_count = models.PositiveIntegerField(default=0)
    being_processed = models.CharField(
        max_length=10, choices=TNKReport.YES_NO, blank=True
    )

    def __str__(self):
        return self.get_title_type_display()


class CulturalKnowledge(models.Model):
    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="cultural_knowledge"
    )
    knowledge_type = models.CharField(max_length=200)
    preservation_plan = models.TextField(blank=True)

    def __str__(self):
        return self.knowledge_type


class Signature(models.Model):
    ROLE = (
        ("liuliu_bose_vakoro", "Liuliu ni Bose Vakoro"),
        ("turaga_ni_koro", "Turaga ni Koro"),
        ("nasi_ni_koro", "Nasi ni Koro"),
        ("roko_veivuke", "Roko Veivuke"),
        ("roko_tui", "Roko Tui"),
    )

    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="signatures"
    )
    role = models.CharField(max_length=50, choices=ROLE)
    name = models.CharField(max_length=150)
    signed = models.BooleanField(default=False)
    signed_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_role_display()} - {self.name}"


class IVDPImplementationSchedule(models.Model):
    report = models.ForeignKey(
        TNKReport, on_delete=models.CASCADE, related_name="ivdp_schedule"
    )
    project = models.CharField(max_length=200)
    responsibility = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    consultation_approval = models.BooleanField(default=False)
    commencement = models.BooleanField(default=False)
    priority_area_achieved_50 = models.BooleanField(default=False)
    project_completion = models.BooleanField(default=False)

    def progress_percentage(self):
        progress = 0
        if self.consultation_approval:
            progress += 25
        if self.commencement:
            progress += 25
        if self.priority_area_achieved_50:
            progress += 25
        if self.project_completion:
            progress += 25
        return progress

    def __str__(self):
        return self.project
