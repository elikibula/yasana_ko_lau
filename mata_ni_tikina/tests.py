from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import TuragaProfile
from koro.models import Koro
from tikina.models import Tikina
from turani.models import PopulationAgeGroup, TNKReport

from .models import CouncilSavingsAccount, MNTReport, VagalalaSettlement


class MataReportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("mata", password="StrongPass123!", first_name="Josaia", last_name="Tawake")
        profile = self.user.turaga_profile
        profile.membership_type = TuragaProfile.MATA_NI_TIKINA
        profile.date_of_birth = date(1975, 2, 2)
        profile.village = "Tubou"
        profile.district = "Lakeba"
        profile.province = "Lau"
        profile.save()
        self.client.force_login(self.user)

    def test_create_report_snapshots_mata_identity(self):
        data = {"quarter": "Q1", "year": "2026", "action": "save_draft"}
        response = self.client.post(reverse("mata_ni_tikina:report_create"), data)
        self.assertEqual(response.status_code, 302)
        report = MNTReport.objects.get()
        self.assertEqual(report.full_name, "Josaia Tawake")
        self.assertEqual(report.tikina, "Lakeba")

    def test_form_and_dashboard_render(self):
        self.assertEqual(self.client.get(reverse("mata_ni_tikina:report_create")).status_code, 200)
        dashboard = self.client.get(reverse("mata_ni_tikina:mata_ni_tikina_dashboard"))
        self.assertContains(dashboard, "Dashboard ni Tikina")
        self.assertContains(dashboard, "Ripote ena Veigauna")

    def test_dashboard_renders_latest_report_analysis(self):
        MNTReport.objects.create(
            owner=self.user,
            quarter="Q1",
            year=2026,
            full_name="Josaia Tawake",
            village="Tubou",
            tikina="Lakeba",
            province="Lau",
            tikina_population=123,
            council_total_attendees=12,
            soli_target_amount=100,
            soli_collected_amount=75,
            soli_balance_amount=25,
        )

        response = self.client.get(reverse("mata_ni_tikina:mata_ni_tikina_dashboard"))

        self.assertContains(response, "Lakeba - Q1 2026")
        self.assertContains(response, "Na ka e dodonu me raici taumada")
        self.assertContains(response, "Veisau ni Soli ena veigauna")

    def test_create_form_does_not_show_delete_checkboxes(self):
        response = self.client.get(reverse("mata_ni_tikina:report_create"))

        self.assertNotContains(response, "-DELETE")

    def test_create_form_seeds_koro_names_for_profile_tikina(self):
        tikina = Tikina.objects.create(number=1, name="LAKEBA", koro_turaga="TUBOU")
        Koro.objects.create(name="Tubou", tikina=tikina, is_koro_turaga=True)
        Koro.objects.create(name="Vakano", tikina=tikina)

        response = self.client.get(reverse("mata_ni_tikina:report_create"))

        self.assertContains(response, "TUBOU")
        self.assertContains(response, "VAKANO")
        self.assertContains(response, "Buli oti vakavanua?")
        self.assertNotContains(response, "VAKADINADINA")

    def test_create_form_sections_render_in_ascending_order(self):
        response = self.client.get(reverse("mata_ni_tikina:report_create"))
        content = response.content.decode()
        expected_order = [
            "1.1-1.6 Tukutuku Raraba",
            "1.7 Na Koro ena loma ni Tikina",
            "1.8 Ai Cavuti Raraba Vakavanua",
            "1.9 Wiliwili Taucoko ni iTikotiko Vagalala",
            "1.10 Soveyataki ni Koro",
            "1.11 Kerekere ni Registertaki ni iTikotiko Vagalala me Koro",
            "2.0 Matabose ni Tikina",
            "3.1-3.4 iTuvaki ni Veisemati kei Cakacakavata",
            "iKuri ni Vakamacala",
            "3.4 Veileti se Leqa e yaco kei na kena i wali",
            "4.1 Development Plan",
            "4.2 Tuvatuva ni Veivakatorocaketaki",
            "4.2(v) Na Vuli",
            "4.2 Lewa ni Matabose me baleta na Vuli",
            "4.3 iVurevure ni Lavo",
            "4.4 Vuli ni Tei Kau",
            "4.5 Vurevure ni Lavo",
            "4.6 Cakacakavata kei na Matanitu",
            "4.7 Vakacakavata kei na veitabana tale eso se NGO",
            "5.1 Na cava soti nai vurevure ni Lavo ni Jikina?",
            "5.2 Lavo ni Matabose ni Jikina",
            "5.3 Soli ni Jikina",
            "5.5 Bolebole ni Kumuni Lavo",
            "5.6 Vakamacala ni Tubucake ni Lavo",
            "6.1 Tuvaki ni Qele ni Teitei",
            "7.0 Vakaitavi ni Vakailesilesi",
            "7.1 iVakatakilakila ni Bolebole",
            "8.0 Veitalevi ena Veikoro",
        ]

        positions = []
        for title in expected_order:
            self.assertIn(title, content)
            positions.append(content.index(title))
        self.assertEqual(positions, sorted(positions))

    def test_finance_section_displays_pdf_form_fields(self):
        response = self.client.get(reverse("mata_ni_tikina:report_create"))

        expected_labels = [
            "5.1 Na cava soti nai vurevure ni Lavo ni Jikina?",
            "5.2 Lavo ni Matabose ni Jikina",
            "E maroroi Lavo tu na Matabose ni Jikina?",
            "Baqe / Soqosoqo",
            "5.3 Soli ni Jikina",
            "Soli e lavaki ena yabaki qo",
            "Wiliwili ni Tamata era Soli",
            "Levu ni Soli ni Yasana sa soli rawa",
            "Vo ni Lavo me Kumuni",
            "Sala ni Kumuni Soli",
            "5.5 Bolebole ni Kumuni Lavo",
            "5.6 Vakamacala ni Tubucake ni Lavo",
        ]
        for label in expected_labels:
            self.assertContains(response, label)
        self.assertContains(response, 'name="savings-0-funds_held"')
        self.assertContains(response, 'name="savings-0-bank"')
        self.assertNotContains(response, "5.4 Maroroi Lavo")
        self.assertNotContains(response, "iVakatagedegede ni maroroi lavo")
        self.assertNotContains(response, "Naba ni Akaude")
        self.assertNotContains(response, "Levu ni Lavo")

        content = response.content.decode()
        ordered_titles = [
            "5.2 Lavo ni Matabose ni Jikina",
            "E maroroi Lavo tu na Matabose ni Jikina?",
            "Baqe / Soqosoqo",
            "5.3 Soli ni Jikina",
        ]
        positions = [content.index(title) for title in ordered_titles]
        self.assertEqual(positions, sorted(positions))

    def test_create_report_saves_repeating_council_savings_rows(self):
        response = self.client.post(
            reverse("mata_ni_tikina:report_create"),
            {
                "quarter": "Q1",
                "year": "2026",
                "savings-TOTAL_FORMS": "1",
                "savings-INITIAL_FORMS": "0",
                "savings-MIN_NUM_FORMS": "0",
                "savings-MAX_NUM_FORMS": "1000",
                "savings-0-funds_held": "io",
                "savings-0-bank": "unit_trust_fiji",
                "action": "save_draft",
            },
        )

        self.assertEqual(response.status_code, 302)
        savings = CouncilSavingsAccount.objects.get(report=MNTReport.objects.get())
        self.assertEqual(savings.funds_held, "io")
        self.assertEqual(savings.bank, "unit_trust_fiji")

    def test_create_report_autocalculates_tikina_population_and_council_total(self):
        tikina = Tikina.objects.create(number=1, name="LAKEBA", koro_turaga="TUBOU")
        Koro.objects.create(name="Tubou", tikina=tikina, is_koro_turaga=True)
        tnk_report = TNKReport.objects.create(
            owner=self.user,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="",
            province="Lau",
            village_headman_name="TNK",
            status=TNKReport.STATUS_SUBMITTED,
        )
        PopulationAgeGroup.objects.create(report=tnk_report, gender="tagane", age_group="0_10", count=12)
        PopulationAgeGroup.objects.create(report=tnk_report, gender="yalewa", age_group="11_20", count=18)

        response = self.client.post(
            reverse("mata_ni_tikina:report_create"),
            {
                "quarter": "Q1",
                "year": "2026",
                "council_turaga_count": "2",
                "council_marama_count": "3",
                "council_daunivakasala_count": "1",
                "action": "save_draft",
            },
        )

        self.assertEqual(response.status_code, 302)
        report = MNTReport.objects.get()
        self.assertEqual(report.tikina_population, 30)
        self.assertEqual(report.council_total_attendees, 6)
        self.assertEqual(report.koro_under_tikina.count(), 1)

    def test_vagalala_totals_are_calculated_from_rows(self):
        response = self.client.post(
            reverse("mata_ni_tikina:report_create"),
            {
                "quarter": "Q1",
                "year": "2026",
                "vagalala-TOTAL_FORMS": "2",
                "vagalala-INITIAL_FORMS": "0",
                "vagalala-MIN_NUM_FORMS": "0",
                "vagalala-MAX_NUM_FORMS": "1000",
                "vagalala-0-settlement_name": "Nasaqalau",
                "vagalala-0-household_head": "Jone",
                "vagalala-0-population_count": "11",
                "vagalala-0-family_count": "3",
                "vagalala-1-settlement_name": "Delaivale",
                "vagalala-1-household_head": "Mere",
                "vagalala-1-population_count": "9",
                "vagalala-1-family_count": "2",
                "action": "save_draft",
            },
        )

        self.assertEqual(response.status_code, 302)
        report = MNTReport.objects.get()
        self.assertEqual(report.vagalala_population_total, 20)
        self.assertEqual(report.vagalala_family_total, 5)
        self.assertEqual(VagalalaSettlement.objects.filter(report=report).count(), 2)

    def test_wrong_membership_cannot_enter_mata_area(self):
        self.user.turaga_profile.membership_type = TuragaProfile.TURAGA_NI_KORO
        self.user.turaga_profile.appointment_date = date(2020, 1, 1)
        self.user.turaga_profile.save()
        response = self.client.get(reverse("mata_ni_tikina:mata_ni_tikina_dashboard"))
        self.assertRedirects(response, reverse("accounts:dashboard"), fetch_redirect_response=False)

    def test_report_exports_as_pdf(self):
        report = MNTReport.objects.create(
            owner=self.user,
            quarter="Q1",
            year=2026,
            full_name="Josaia Tawake",
            village="Tubou",
            tikina="Lakeba",
            province="Lau",
            council_head_name="Josaia Tawake",
            status=MNTReport.STATUS_APPROVED_BY_ROKO,
        )

        response = self.client.get(reverse("mata_ni_tikina:report_pdf", args=[report.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
