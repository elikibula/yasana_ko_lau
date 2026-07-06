from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import TuragaProfile, UserProfile
from koro.models import Koro, KoroReport
from mata_ni_tikina.models import (
    CouncilSavingsAccount,
    FundCollectionChallenge,
    IncomeSourceItem,
    KoroUnderTikina,
    MNTReport,
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
from tikina.models import Tikina, TikinaReport
from turaga_ni_yavusa.models import Signature as TNYSignature
from turaga_ni_yavusa.models import TNYReport
from turani.models import (
    Business,
    BusinessTraining,
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
    Signature as TNKSignature,
    TNKApprovalAction,
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
from yavusa.models import YavusaReport


VULAGA_KORO = [
    {"name": "MUANAICAKE", "is_koro_turaga": True, "population": 142},
    {"name": "MUANAIRA", "is_koro_turaga": False, "population": 118},
    {"name": "NAIVIDAMU", "is_koro_turaga": False, "population": 96},
    {"name": "OGEA", "is_koro_turaga": False, "population": 84},
]

LIULIU = [
    {
        "koro": "MUANAICAKE",
        "first_name": "Jone",
        "last_name": "Vulaga",
        "yavusa": "Yavusa Muanaicake",
        "mataqali": "Mataqali Vatu",
        "tokatoka": "Tokatoka Nasau",
        "phone": "6797006101",
    },
    {
        "koro": "MUANAIRA",
        "first_name": "Mere",
        "last_name": "Muanaira",
        "yavusa": "Yavusa Muanaira",
        "mataqali": "Mataqali Wai",
        "tokatoka": "Tokatoka Cagi",
        "phone": "6797006102",
    },
    {
        "koro": "NAIVIDAMU",
        "first_name": "Pita",
        "last_name": "Naividamu",
        "yavusa": "Yavusa Naividamu",
        "mataqali": "Mataqali Toba",
        "tokatoka": "Tokatoka Dravuni",
        "phone": "6797006103",
    },
    {
        "koro": "OGEA",
        "first_name": "Adi Ana",
        "last_name": "Ogea",
        "yavusa": "Yavusa Ogea",
        "mataqali": "Mataqali Saku",
        "tokatoka": "Tokatoka Nuku",
        "phone": "6797006104",
    },
]


class Command(BaseCommand):
    help = "Seed idempotent dummy Vulaga/Fulaga data for report analytics."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="VulagaDemo123!",
            help="Password assigned to the dummy users.",
        )
        parser.add_argument("--quarter", default="Q2")
        parser.add_argument("--year", type=int, default=timezone.localdate().year)

    @transaction.atomic
    def handle(self, *args, **options):
        self.password = options["password"]
        self.quarter = options["quarter"]
        self.year = options["year"]

        tikina = self._seed_tikina()
        koro_by_name = self._seed_koro(tikina)
        mata_user = self._seed_mata_ni_tikina(tikina)
        tnk_users = self._seed_turaga_ni_koro(tikina, koro_by_name)
        liuliu_users = self._seed_liuliu_ni_yavusa(tikina)

        self._seed_tnk_reports(tikina, tnk_users)
        self._seed_mnt_report(tikina, mata_user)
        self._seed_tny_reports(tikina, liuliu_users)
        self._seed_legacy_summary_reports(tikina, tnk_users, mata_user, liuliu_users)

        self.stdout.write(self.style.SUCCESS("Seeded Vulaga dummy data."))
        self.stdout.write(f"  Tikina: {tikina.name}")
        self.stdout.write("  Koro: " + ", ".join(koro_by_name.keys()))
        self.stdout.write(f"  Mata ni Tikina login: {mata_user.username} / {self.password}")
        self.stdout.write(
            "  Liuliu ni Yavusa logins: "
            + ", ".join(user.username for user in liuliu_users.values())
            + f" / {self.password}"
        )
        self.stdout.write(
            "  Turaga ni Koro logins: "
            + ", ".join(user.username for user in tnk_users.values())
            + f" / {self.password}"
        )

    def _seed_tikina(self):
        tikina, _ = Tikina.objects.get_or_create(
            number=6,
            defaults={
                "name": "FULAGA",
                "koro_turaga": "MUANAICAKE",
                "official_koro_count": 4,
                "island_group": "Southern Lau",
            },
        )
        tikina.name = "FULAGA"
        tikina.koro_turaga = "MUANAICAKE"
        tikina.official_koro_count = 4
        tikina.island_group = "Southern Lau"
        tikina.population = sum(item["population"] for item in VULAGA_KORO)
        tikina.mataqali_count = 8
        tikina.description = "Dummy Vulaga/Fulaga dataset for local analytics testing."
        tikina.is_active = True
        tikina.save()
        return tikina

    def _seed_koro(self, tikina):
        created = {}
        for item in VULAGA_KORO:
            if item["is_koro_turaga"]:
                tikina.koro.filter(is_koro_turaga=True).exclude(name=item["name"]).update(is_koro_turaga=False)
            koro, _ = Koro.objects.get_or_create(
                name=item["name"],
                tikina=tikina,
                defaults={"is_koro_turaga": item["is_koro_turaga"]},
            )
            koro.is_koro_turaga = item["is_koro_turaga"]
            koro.population = item["population"]
            koro.notes = "Dummy Vulaga analytics seed"
            koro.description = f"Dummy profile data for {item['name']} in Vulaga/Fulaga."
            koro.save()
            created[koro.name] = koro
        return created

    def _user(self, username, first_name, last_name, email, role, *, is_staff=False):
        User = get_user_model()
        user, _ = User.objects.get_or_create(username=username)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_active = True
        user.is_staff = is_staff
        user.set_password(self.password)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.phone = profile.phone or "6797006000"
        profile.save()

        for group_name in [
            UserProfile.TURAGA_NI_KORO,
            UserProfile.MATA_NI_TIKINA,
            UserProfile.LIULIU_NI_YAVUSA,
            UserProfile.ROKO_ADMIN,
        ]:
            Group.objects.get_or_create(name=group_name)
        user.groups.add(Group.objects.get(name=role))
        user.groups.remove(
            *Group.objects.filter(
                name__in=[
                    UserProfile.TURAGA_NI_KORO,
                    UserProfile.MATA_NI_TIKINA,
                    UserProfile.LIULIU_NI_YAVUSA,
                    UserProfile.ROKO_ADMIN,
                ]
            ).exclude(name=role)
        )
        return user

    def _seed_mata_ni_tikina(self, tikina):
        user = self._user(
            "vulaga.mata",
            "Samuela",
            "Mata ni Tikina",
            "vulaga.mata@example.test",
            UserProfile.MATA_NI_TIKINA,
        )
        user.user_profile.tikina = tikina.name
        user.user_profile.koro = "MUANAICAKE"
        user.user_profile.phone = "6797006200"
        user.user_profile.save()

        profile = user.turaga_profile
        profile.membership_type = TuragaProfile.MATA_NI_TIKINA
        profile.date_of_birth = date(1978, 3, 12)
        profile.village = "MUANAICAKE"
        profile.district = tikina.name
        profile.province = "LAU"
        profile.phone_number = "6797006200"
        profile.save()

        tikina.mata_ni_tikina = user.user_profile
        tikina.save(update_fields=["mata_ni_tikina"])
        return user

    def _seed_turaga_ni_koro(self, tikina, koro_by_name):
        users = {}
        for index, item in enumerate(VULAGA_KORO, start=1):
            koro_name = item["name"]
            user = self._user(
                f"vulaga.tnk.{koro_name.lower()}",
                ["Isikeli", "Siteri", "Tomasi", "Litia"][index - 1],
                koro_name.title(),
                f"vulaga.tnk.{koro_name.lower()}@example.test",
                UserProfile.TURAGA_NI_KORO,
            )
            user.user_profile.tikina = tikina.name
            user.user_profile.koro = koro_name
            user.user_profile.phone = f"67970063{index:02d}"
            user.user_profile.save()

            profile = user.turaga_profile
            profile.membership_type = TuragaProfile.TURAGA_NI_KORO
            profile.date_of_birth = date(1970 + index, 2, 10)
            profile.appointment_date = date(2025, index, 1)
            profile.village = koro_name
            profile.district = tikina.name
            profile.province = "LAU"
            profile.phone_number = user.user_profile.phone
            profile.save()

            koro = koro_by_name[koro_name]
            koro.turaga_ni_koro = user.user_profile
            koro.save(update_fields=["turaga_ni_koro"])
            users[koro_name] = user
        return users

    def _seed_liuliu_ni_yavusa(self, tikina):
        users = {}
        for item in LIULIU:
            user = self._user(
                f"vulaga.liuliu.{item['koro'].lower()}",
                item["first_name"],
                item["last_name"],
                f"vulaga.liuliu.{item['koro'].lower()}@example.test",
                UserProfile.LIULIU_NI_YAVUSA,
            )
            user.user_profile.tikina = tikina.name
            user.user_profile.koro = item["koro"]
            user.user_profile.yavusa = item["yavusa"]
            user.user_profile.phone = item["phone"]
            user.user_profile.save()

            profile = user.turaga_profile
            profile.membership_type = TuragaProfile.TURAGA_NI_YAVUSA
            profile.date_of_birth = date(1974, 6, 1)
            profile.village = item["koro"]
            profile.district = tikina.name
            profile.province = "LAU"
            profile.phone_number = item["phone"]
            profile.tokatoka = item["tokatoka"]
            profile.mataqali = item["mataqali"]
            profile.yavusa = item["yavusa"]
            profile.vanua = "Vulaga"
            profile.save()
            users[item["koro"]] = user
        return users

    def _tnk_report_defaults(self, tikina, koro_name, owner, index):
        population = VULAGA_KORO[index - 1]["population"]
        return {
            "owner": owner,
            "quarter": self.quarter,
            "year": self.year,
            "village": koro_name,
            "district": tikina.name,
            "province": "LAU",
            "village_headman_name": owner.get_full_name(),
            "village_headman_age": 44 + index,
            "appointment_month_year": f"0{index}/2025",
            "village_meetings_count": 2 + index,
            "household_count": max(16, population // 5),
            "correction_reintegration_plan": "Dummy reintegration support plan recorded for analytics.",
            "water_problem_responsible_agency": "Village water committee and WAF.",
            "water_challenges": "Intermittent rainwater storage pressure during dry weeks.",
            "water_sanitation_challenges": "Some household tanks need repair.",
            "toilet_wastewater_agency": "Village health committee.",
            "toilet_wastewater_challenges": "Two households flagged for follow-up.",
            "ivdp_progress_started": "io",
            "ivdp_unfinished_reason": "",
            "yaubula_current_plan": "Coastal cleanup and reef awareness activity.",
            "yaubula_management_plan": "Quarterly yaubula inspection and youth cleanup rotation.",
            "disaster_current_plan": "Evacuation roster and radio contact tree maintained.",
            "disaster_future_plan": "Update cyclone supplies before Q4.",
            "has_evacuation_centre": "io",
            "evacuation_centre_capacity": 70 + (index * 8),
            "has_male_female_restrooms": "io",
            "climate_change_impact": "io",
            "climate_change_impact_details": "Coastal erosion and salt spray affecting gardens.",
            "climate_change_solution_done": "io",
            "climate_change_solution_details": "Mangrove planting and seawall maintenance.",
            "bose_vanua_count": 1 + index,
            "status": TNKReport.STATUS_SUBMITTED_TO_MATA,
            "submitted_at": timezone.now(),
        }

    def _seed_tnk_reports(self, tikina, tnk_users):
        for index, (koro_name, owner) in enumerate(tnk_users.items(), start=1):
            report, _ = TNKReport.objects.update_or_create(
                owner=owner,
                quarter=self.quarter,
                year=self.year,
                defaults=self._tnk_report_defaults(tikina, koro_name, owner, index),
            )
            self._replace_tnk_children(report, index)

    def _replace_tnk_children(self, report, index):
        child_managers = [
            report.visits,
            report.meeting_decisions,
            report.committees,
            report.law_offences,
            report.correction_returnees,
            report.trainings,
            report.population,
            report.housing_counts,
            report.water_sources,
            report.water_committee_answers,
            report.water_committee_members,
            report.toilet_types,
            report.electricity_sources,
            report.health_conditions,
            report.disabilities,
            report.crops,
            report.ivdp_projects,
            report.ivdp_schedule,
            report.businesses,
            report.business_trainings,
            report.assets_savings,
            report.evacuation_centre_materials,
            report.traditional_titles,
            report.cultural_knowledge,
            report.signatures,
            report.approval_actions,
        ]
        for manager in child_managers:
            manager.all().delete()
        WasteManagement.objects.filter(report=report).delete()

        Visit.objects.create(report=report, visit_type="yasana", officer_name="Roko Veivuke Dummy", visit_date=date(self.year, 6, 5), purpose="Quarterly support visit.")
        Visit.objects.create(report=report, visit_type="government", officer_name="Health Inspector Dummy", visit_date=date(self.year, 6, 18), purpose="Water and sanitation checks.")
        VillageMeetingDecision.objects.create(report=report, decision="Repair community water tank guttering.", implemented="io")
        VillageMeetingDecision.objects.create(report=report, decision="Complete village cleanup before Bose ni Tikina.", implemented="sega", reason_not_implemented="Materials awaiting boat transport.")
        for committee, male, female in [("development", 4, 3), ("water", 3, 2), ("women", 0, 6), ("youth", 5, 4)]:
            VillageCommittee.objects.create(report=report, committee_type=committee, exists="io", male_members=male + index, female_members=female, meetings_last_3_months=index)
        LawOffence.objects.create(report=report, offence_name="Minor village by-law breach", count=index, reported_to_law="sega", reason_not_reported="Resolved by village committee.")
        Training.objects.create(report=report, training_type="vanua", title="Vulaga leadership refresher", organization="Yasana ko Lau", date=date(self.year, 5, 20), participants_count=12 + index, outcome="Reporting process improved.")
        for gender, age_counts in {
            "tagane": [12 + index, 9 + index, 8 + index, 7 + index, 6, 5, 4],
            "yalewa": [11 + index, 10 + index, 9 + index, 8, 7, 5, 4],
        }.items():
            for age_group, count in zip(["0_10", "11_20", "21_30", "31_40", "41_50", "51_60", "61_plus"], age_counts):
                PopulationAgeGroup.objects.create(report=report, gender=gender, age_group=age_group, count=count)
        for house_type, material, count in [("house", "simede", 12 + index), ("house", "kau", 8), ("kitchen", "kau", 10), ("toilet", "simede", 14)]:
            HousingCount.objects.create(report=report, house_type=house_type, material=material, count=count)
        for source in ["wai_ni_uca", "taqe_ni_wai", "waf"]:
            WaterSource.objects.create(report=report, source=source, selected=True)
        for question, answer in WaterCommitteeQuestion.QUESTIONS:
            WaterCommitteeQuestion.objects.create(report=report, question=question, answer=question != "log_book")
        for member in ["Chair", "Secretary", "Maintenance Lead"]:
            WaterCommitteeMember.objects.create(report=report, name=f"{member} {report.village.title()}")
        WasteManagement.objects.create(report=report, village_dump="io", village_boundary_clean="io", household_dump="io", garbage_truck="sega")
        ToiletType.objects.create(report=report, toilet_type="septic_simede", count=12 + index)
        ToiletType.objects.create(report=report, toilet_type="keli", count=3)
        ElectricitySource.objects.create(report=report, source="solar", house_count=18 + index)
        ElectricitySource.objects.create(report=report, source="private_generator", house_count=4)
        HealthConditionCount.objects.create(report=report, condition_name="Diabetes", age_group="36_60", count=2 + index)
        DisabilityCount.objects.create(report=report, disability_name="Mobility support required", age_group="60_plus", count=1)
        CropCount.objects.create(report=report, category="kakana_dina", crop_name="Dalo", plantation_count=10 + index)
        CropCount.objects.create(report=report, category="kakana_draudrau", crop_name="Rourou", plantation_count=6 + index)
        project = IVDPProject.objects.create(
            report=report,
            project_name=f"{report.village.title()} water storage upgrade",
            project_number=index,
            priority_area=2,
            work_done="Community consultation completed.",
            application_prepared="io",
            funding_agency="Provincial Office",
            materials_received="sega",
            problem_reason="Transport delay.",
            solution="Coordinate with next scheduled vessel.",
        )
        IVDPImplementationSchedule.objects.create(report=report, project=project.project_name, responsibility="Village committee", organization="Yasana ko Lau", start_date=date(self.year, 5, 1), end_date=date(self.year, 8, 30), consultation_approval=True, commencement=True)
        Business.objects.create(report=report, business_name=f"{report.village.title()} canteen", owner_name="Dummy Owner", licensed="io", business_type="Retail", years_running="3")
        BusinessTraining.objects.create(report=report, course_name="Small business basics", organization="Ministry of Trade", date=date(self.year, 6, 1), participants_count=6 + index, outcome="Bookkeeping templates adopted.")
        for question in ["assets", "investment", "savings"]:
            VillageAssetSaving.objects.create(report=report, question=question, answer="io", description="Dummy finance entry for analysis.")
        EvacuationCentreMaterial.objects.create(report=report, material="simede", selected=True)
        TraditionalTitleStatus.objects.create(report=report, title_type="turaga_ni_yavusa", yavusa_mataqali_count=2, confirmed_count=1, unconfirmed_count=1, being_processed="io")
        CulturalKnowledge.objects.create(report=report, knowledge_type="Vosa vakavanua", preservation_plan="Monthly talanoa with elders.")
        TNKSignature.objects.create(report=report, role="turaga_ni_koro", name=report.village_headman_name, signed=True, signed_date=date(self.year, 6, 30))
        TNKApprovalAction.objects.create(
            report=report,
            user=report.owner,
            user_full_name=report.village_headman_name,
            user_role="Turaga ni Koro",
            action_type=TNKApprovalAction.ACTION_SUBMIT,
            from_status=TNKReport.STATUS_DRAFT,
            to_status=TNKReport.STATUS_SUBMITTED_TO_MATA,
            comment="Dummy report submitted for analytics.",
            digital_acknowledgement="Dummy acknowledgement for local testing.",
        )

    def _seed_mnt_report(self, tikina, owner):
        report, _ = MNTReport.objects.update_or_create(
            owner=owner,
            quarter=self.quarter,
            year=self.year,
            defaults={
                "full_name": owner.get_full_name(),
                "age": 48,
                "village": "MUANAICAKE",
                "tikina": tikina.name,
                "province": "LAU",
                "tikina_population": tikina.population,
                "announcements_made_count": "Four announcements circulated to all Vulaga Koro.",
                "traditional_announcements_received_count": "Three items received from village leaders.",
                "vagalala_population_total": 24,
                "vagalala_family_total": 5,
                "villages_surveyed_count": 4,
                "villages_pending_survey_count": 0,
                "council_head_name": owner.get_full_name(),
                "council_head_age": "48",
                "council_turaga_count": 12,
                "council_marama_count": 10,
                "council_daunivakasala_count": 4,
                "council_total_attendees": 26,
                "council_meeting_frequency": "Monthly",
                "council_additional_notes": "Dummy Vulaga council meeting notes.",
                "coordination_additional_notes": "All Koro represented in the dummy dataset.",
                "has_development_plan": "io",
                "education_council_decision": "Support exam transport and boarding needs.",
                "education_next_quarter_decision": "Run study support talanoa.",
                "income_trend": "tubucake",
                "income_council_decision": "Coordinate handicraft market days.",
                "infrastructure_trend": "rawa_vakatikina",
                "villages_with_phone_count": 4,
                "villages_with_tv_count": 3,
                "boat_count": 9,
                "vehicle_count": 1,
                "villages_with_road_access_count": 0,
                "development_council_decision": "Prioritize water storage.",
                "govt_financial_assistance_amount": Decimal("12000.00"),
                "govt_assisting_department": "Provincial Office",
                "govt_official_visits_count": 2,
                "govt_projects_covered": "Water storage and sanitation.",
                "govt_partnership_notes": "Dummy partnership notes.",
                "ngo_awareness_programs_notes": "Climate resilience awareness.",
                "ngo_financial_assistance_amount": Decimal("3500.00"),
                "ngo_program_name": "Community resilience",
                "ngo_project_equipment_value": Decimal("2000.00"),
                "ngo_project_name": "Water tank repair kits",
                "ngo_partnership_notes": "Dummy NGO partnership notes.",
                "council_funds_held": "io",
                "soli_target_amount": Decimal("8000.00"),
                "soli_contributor_count": 96,
                "soli_collected_amount": Decimal("5400.00"),
                "soli_balance_amount": Decimal("2600.00"),
                "soli_collection_method": "Village committee collections.",
                "fund_growth_notes": "Collections tracking upward.",
                "has_registered_farmland": "io",
                "farmland_lease_count": 4,
                "farmland_acres_leased": Decimal("12.50"),
                "farmland_lease_years_covered": "2024-2026",
                "farmland_development_notes": "Dummy farmland development note.",
                "reps_attend_meetings": "io",
                "reps_understand_training_needs": "io",
                "reps_assist_report_writing": "io",
                "reps_help_outside_meetings": "io",
                "reps_additional_notes": "Representatives active across all four Koro.",
                "reps_council_decision": "Continue monthly reporting support.",
                "status": MNTReport.STATUS_SUBMITTED,
                "submitted_at": timezone.now(),
            },
        )
        self._replace_mnt_children(report)

    def _replace_mnt_children(self, report):
        for manager in [
            report.koro_under_tikina,
            report.vagalala_settlements,
            report.settlement_registrations,
            report.coordination_statuses,
            report.disputes,
            report.social_indicators,
            report.education_trainings,
            report.income_sources,
            report.tree_planting_trainings,
            report.income_activities,
            report.savings_accounts,
            report.fund_challenges,
            report.challenge_indicators,
            report.village_visits,
            report.signatures,
        ]:
            manager.all().delete()

        for item in VULAGA_KORO:
            KoroUnderTikina.objects.create(report=report, village_name=item["name"], traditional_leader=f"Turaga {item['name'].title()}", installed="io")
            TikinaVillageVisit.objects.create(report=report, visit_date=date(self.year, 6, 10), village_name=item["name"], role_performed="Dummy monitoring visit and report support.", turaga_ni_koro_confirmation="Confirmed")
        VagalalaSettlement.objects.create(report=report, settlement_name="Dummy Vulaga Settlement", household_head="Test Household", population_count=24, family_count=5)
        for entity in ["yavusa_leadership", "mataqali_leadership", "church_leadership", "organization_leadership"]:
            TikinaCoordinationStatus.objects.create(report=report, entity=entity, status="matata")
        TikinaDispute.objects.create(report=report, description="Boundary discussion for dummy analysis.", resolution="Mediated by Tikina council.")
        TikinaDispute.objects.create(report=report, description="Open resource-use discussion for dummy analysis.", resolution="")
        for indicator, trend in [("spiritual_life", "tubucake"), ("traditional_custom", "rawa_vakatikina"), ("drinking_water", "rawa_vakatikina"), ("food_supply", "tubucake"), ("education", "tubucake")]:
            TikinaSocialIndicator.objects.create(report=report, indicator=indicator, trend=trend)
        TikinaEducationTraining.objects.create(report=report, training_type="Report writing", training_leader="Mata ni Tikina", participants_count=18, benefit="Improved data quality.")
        for category, count in [("business", 4), ("farming", 7), ("fishing", 9), ("handicrafts", 6)]:
            IncomeSourceItem.objects.create(report=report, category=category, ownership_or_detail="Dummy Vulaga activity", count_or_amount=count)
        TreePlantingTraining.objects.create(report=report, tree_type="traditional", training_conducted="io", training_leader="Yaubula committee", participants_count=14, villager_benefit="Coastal protection awareness.")
        for activity in ["qoli_volitaki_ika", "dalo", "sasalu_waitui", "liga_buliyaya"]:
            TikinaIncomeActivity.objects.create(report=report, activity=activity, selected=True)
        CouncilSavingsAccount.objects.create(report=report, funds_held="io", bank="anz", saving_level="vakoro", account_number="DUMMY-VULAGA-001", amount=Decimal("5400.00"))
        for challenge in ["no_boat_or_lorry", "no_market", "low_produce_price"]:
            FundCollectionChallenge.objects.create(report=report, challenge=challenge, selected=True)
        for indicator in ["solesolevaki", "makete", "waqa", "vodovodo"]:
            TikinaChallengeIndicator.objects.create(report=report, indicator=indicator, selected=True)

    def _seed_tny_reports(self, tikina, liuliu_users):
        for index, item in enumerate(LIULIU, start=1):
            owner = liuliu_users[item["koro"]]
            report, _ = TNYReport.objects.update_or_create(
                owner=owner,
                quarter=self.quarter,
                year=self.year,
                defaults={
                    "full_name": owner.get_full_name(),
                    "phone_number": item["phone"],
                    "email": owner.email,
                    "tokatoka": item["tokatoka"],
                    "mataqali": item["mataqali"],
                    "yavusa": item["yavusa"],
                    "vanua": "Vulaga",
                    "koro": item["koro"],
                    "tikina": tikina.name,
                    "bosevanua_meeting_frequency": "2",
                    "bosevanua_turaga_ni_mataqali_count": 2 + index,
                    "bosevanua_liuliu_ni_tokatoka_count": 3 + index,
                    "bosevanua_lewe_ni_yavusa_count": 46 + (index * 7),
                    "genealogy_recorded_count": 6 + index,
                    "genealogy_removed_count": index - 1,
                    "yavusa_report_filed": "io",
                    "yavusa_report_topics": "Genealogy, land care, church coordination.",
                    "yavusa_report_notes": "Dummy Vulaga Yavusa meeting notes.",
                    "confirmed_titles_this_period": index,
                    "titles_additional_notes": "Dummy title update.",
                    "language_custom_initiatives": "Youth talanoa with elders.",
                    "land_initiatives": "Clean boundary notes and planting.",
                    "fishing_ground_initiatives": "Qoliqoli awareness session.",
                    "resident_turaga_count": 18 + index,
                    "resident_marama_count": 20 + index,
                    "resident_gone_count": 15 + index,
                    "away_turaga_count": 4 + index,
                    "away_marama_count": 3 + index,
                    "away_gone_count": 2 + index,
                    "has_member_visitation_plan": "io",
                    "attends_bose_vakoro": "io",
                    "attends_bose_ni_tikina": "io",
                    "churches_in_yavusa_count": 2,
                    "church_follows_vanua_program": "io",
                    "church_meets_vanua_needs": "io",
                    "yavusa_obligations": "Dummy Yavusa obligations tracked.",
                    "mataqali_obligations": "Dummy Mataqali obligations tracked.",
                    "tokatoka_obligations": "Dummy Tokatoka obligations tracked.",
                    "status": TNYReport.STATUS_SUBMITTED,
                    "submitted_at": timezone.now(),
                },
            )
            report.signatures.all().delete()
            TNYSignature.objects.create(report=report, role="turaga_ni_yavusa", name=owner.get_full_name(), signed=True, signed_date=date(self.year, 6, 30))
            TNYSignature.objects.create(report=report, role="turaga_ni_koro", name=f"Turaga {item['koro'].title()}", signed=True, signed_date=date(self.year, 6, 30))

    def _seed_legacy_summary_reports(self, tikina, tnk_users, mata_user, liuliu_users):
        for koro_name, user in tnk_users.items():
            KoroReport.objects.update_or_create(
                submitted_by=user,
                koro_name=koro_name,
                tikina=tikina,
                report_type="population",
                defaults={
                    "content": f"Dummy Koro summary report for {koro_name} in Vulaga.",
                    "status": "approved",
                },
            )
        TikinaReport.objects.update_or_create(
            submitted_by=mata_user,
            tikina=tikina,
            report_type="general",
            defaults={
                "summary": "Dummy Mata ni Tikina summary report for Vulaga analytics.",
                "status": "approved",
            },
        )
        for item in LIULIU:
            user = liuliu_users[item["koro"]]
            YavusaReport.objects.update_or_create(
                submitted_by=user,
                yavusa_name=item["yavusa"],
                defaults={
                    "member_count": 60 + len(item["yavusa"]),
                    "content": f"Dummy Yavusa summary report for {item['yavusa']}.",
                    "status": "approved",
                },
            )
