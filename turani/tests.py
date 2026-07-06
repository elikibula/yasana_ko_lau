from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import BusinessTraining, TNKApprovalAction, TNKReport, VillageCommittee


class ReportOwnershipTests(TestCase):
    def make_turaga(self, username, village):
        user = get_user_model().objects.create_user(
            username=username,
            password="StrongPass123!",
            first_name=username.title(),
            last_name="Turaga",
        )
        profile = user.turaga_profile
        profile.date_of_birth = date(1980, 1, 1)
        profile.appointment_date = date(2022, 7, 1)
        profile.village = village
        profile.district = "Lakeba"
        profile.province = "Lau"
        profile.save()
        return user

    def make_mata(self, username, district="Lakeba"):
        user = get_user_model().objects.create_user(
            username=username,
            password="StrongPass123!",
            first_name=username.title(),
            last_name="Mata",
        )
        profile = user.turaga_profile
        profile.membership_type = "mata_ni_tikina"
        profile.date_of_birth = date(1980, 1, 1)
        profile.village = "Tubou"
        profile.district = district
        profile.province = "Lau"
        profile.save()
        Group.objects.get_or_create(name="mata_ni_tikina")[0].user_set.add(user)
        return user

    def empty_formset_data(self):
        data = {}
        for prefix in ("population", "offences", "health", "business", "ivdp"):
            data.update(
                {
                    f"{prefix}-TOTAL_FORMS": "0",
                    f"{prefix}-INITIAL_FORMS": "0",
                    f"{prefix}-MIN_NUM_FORMS": "0",
                    f"{prefix}-MAX_NUM_FORMS": "1000",
                }
            )
        return data

    def test_report_automatically_snapshots_account_details(self):
        user = self.make_turaga("jone", "Tubou")
        self.client.force_login(user)
        data = {
            "quarter": "Q1",
            "year": "2026",
            "village_meetings_count": "3",
            "household_count": "42",
            **self.empty_formset_data(),
        }

        response = self.client.post(reverse("turani:report_create"), data)

        report = TNKReport.objects.get()
        self.assertRedirects(response, reverse("turani:report_edit", args=[report.pk]))
        self.assertEqual(report.owner, user)
        self.assertEqual(report.status, TNKReport.STATUS_DRAFT)
        self.assertEqual(report.village, "Tubou")
        self.assertEqual(report.village_headman_name, "Jone Turaga")
        self.assertEqual(report.appointment_month_year, "July 2022")
        self.assertEqual(report.village_headman_age, 46)

    def test_turaga_cannot_view_another_turagas_report(self):
        owner = self.make_turaga("owner", "Tubou")
        other = self.make_turaga("other", "Levuka")
        report = TNKReport.objects.create(
            owner=owner,
            quarter="Q2",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Owner Turaga",
        )
        self.client.force_login(other)

        response = self.client.get(reverse("turani:report_detail", args=[report.pk]))

        self.assertEqual(response.status_code, 404)

    def test_report_saves_village_committee_details(self):
        user = self.make_turaga("jone", "Tubou")
        self.client.force_login(user)
        data = {
            "quarter": "Q1",
            "year": "2026",
            "village_meetings_count": "3",
            "household_count": "42",
            "committees-TOTAL_FORMS": "1",
            "committees-INITIAL_FORMS": "0",
            "committees-MIN_NUM_FORMS": "0",
            "committees-MAX_NUM_FORMS": "1000",
            "committees-0-committee_type": "development",
            "committees-0-exists": "io",
            "committees-0-male_members": "4",
            "committees-0-female_members": "6",
            "committees-0-meetings_last_3_months": "2",
        }

        response = self.client.post(reverse("turani:report_create"), data)

        report = TNKReport.objects.get()
        committee = report.committees.get()
        self.assertRedirects(response, reverse("turani:report_edit", args=[report.pk]))
        self.assertEqual(committee.committee_type, "development")
        self.assertEqual(committee.total_members(), 10)
        self.assertEqual(committee.meetings_last_3_months, 2)
        self.assertEqual(VillageCommittee.objects.count(), 1)

    def test_report_form_displays_all_village_committee_rows(self):
        user = self.make_turaga("jone", "Tubou")
        self.client.force_login(user)

        response = self.client.get(reverse("turani:report_create"))

        self.assertContains(response, "2.1 Na Komiti Cava Soti")
        self.assertContains(response, 'name="committees-0-committee_type"')
        self.assertContains(response, 'name="committees-7-committee_type"')
        self.assertNotContains(response, '<select name="committees-0-committee_type"')
        self.assertContains(response, "Veivakatorocaketaki")

    def test_report_form_follows_the_tnk_template_section_order(self):
        user = self.make_turaga("jone", "Tubou")
        self.client.force_login(user)

        response = self.client.get(reverse("turani:report_create"))
        content = response.content.decode()

        self.assertLess(
            content.index("ULUTAGA 1: VEILIUTAKI VINAKA"),
            content.index("ULUTAGA 2: TIKO VINAKA NI iTAUKEI"),
        )
        self.assertLess(
            content.index("2.1 Na Komiti Cava Soti"),
            content.index("3.0 Basuki ni Lawa ni Matanitu"),
        )
        self.assertLess(
            content.index("ULUTAGA 3: NA BULA TOROCAKE"),
            content.index("ULUTAGA 4: TAQOMAKI"),
        )
        self.assertLess(
            content.index("17.0 Veiliutaki Vakavanua"),
            content.index("17.1 E dabe vakavica"),
        )
        self.assertNotIn("Saini Eke", content)

    def test_report_form_includes_the_missing_pdf_fields_and_add_row_controls(self):
        user = self.make_turaga("jone", "Tubou")
        self.client.force_login(user)

        response = self.client.get(reverse("turani:report_create"))

        self.assertContains(response, "water_sanitation_challenges")
        self.assertContains(response, "toilet_wastewater_challenges")
        self.assertContains(response, "13.1 Na Vuli ni Cicivaki Bisinisi")
        self.assertNotContains(response, 'name="law-0-DELETE"')
        self.assertNotContains(response, 'name="decisions-0-DELETE"')
        self.assertNotContains(response, 'name="returnees-0-DELETE"')
        self.assertContains(response, 'data-add-row="decisions"')
        self.assertContains(response, 'data-add-row="returnees"')
        self.assertContains(response, 'data-add-row="biztrain"')
        self.assertContains(response, 'name="pop-13-gender"')
        self.assertContains(response, 'name="housing-15-house_type"')
        self.assertContains(response, 'name="wsrc-5-source"')
        self.assertContains(response, 'name="toilet-6-toilet_type"')
        self.assertContains(response, 'name="elec-7-source"')
        self.assertContains(response, 'name="evac-3-material"')
        self.assertContains(response, 'name="titles-1-title_type"')
        self.assertNotContains(response, 'name="sigs-4-role"')
        self.assertContains(response, "Na Lawa e Basuki")
        self.assertContains(response, "Yaca ni Bisinisi")
        self.assertContains(response, "Insert New Record")
        self.assertContains(response, "Kena Levu")
        self.assertContains(response, "Nai wiliwili ni matavuvale")
        self.assertContains(response, "13.0 Bisinisi")
        self.assertContains(response, "E tiko beka e so nai Yau Tudei ni Koro?")
        self.assertContains(response, "E vakatubui lavo tiko na koro? (Investment)")
        self.assertContains(response, "E maroroi lavo tu na koro? (Baqe/Stock Exchange)")

    def test_report_saves_business_training_details(self):
        user = self.make_turaga("jone", "Tubou")
        self.client.force_login(user)
        data = {
            "quarter": "Q1",
            "year": "2026",
            "village_meetings_count": "3",
            "household_count": "42",
            "biztrain-TOTAL_FORMS": "1",
            "biztrain-INITIAL_FORMS": "0",
            "biztrain-MIN_NUM_FORMS": "0",
            "biztrain-MAX_NUM_FORMS": "1000",
            "biztrain-0-course_name": "Vuli ni Cicivaki Bisinisi",
            "biztrain-0-organization": "TAB",
            "biztrain-0-date": "2026-06-01",
            "biztrain-0-purpose": "Vakatubui lavo",
            "biztrain-0-participants_count": "12",
            "biztrain-0-outcome": "Sa vakayacori vinaka",
        }

        response = self.client.post(reverse("turani:report_create"), data)

        report = TNKReport.objects.get()
        training = report.business_trainings.get()
        self.assertRedirects(response, reverse("turani:report_edit", args=[report.pk]))
        self.assertEqual(training.course_name, "Vuli ni Cicivaki Bisinisi")
        self.assertEqual(training.participants_count, 12)
        self.assertEqual(BusinessTraining.objects.count(), 1)

    def test_report_can_be_finally_submitted_after_draft_work(self):
        user = self.make_turaga("jone", "Tubou")
        self.client.force_login(user)
        data = {
            "quarter": "Q1",
            "year": "2026",
            "village_meetings_count": "3",
            "household_count": "42",
            "action": "submit_report",
        }

        response = self.client.post(reverse("turani:report_create"), data)

        report = TNKReport.objects.get()
        self.assertRedirects(response, reverse("turani:report_detail", args=[report.pk]))
        self.assertEqual(report.status, TNKReport.STATUS_SUBMITTED)
        self.assertIsNotNone(report.submitted_at)
        self.assertEqual(report.approval_actions.filter(action_type=TNKApprovalAction.ACTION_SUBMIT).count(), 1)

    def test_turaga_cannot_edit_report_under_review(self):
        user = self.make_turaga("jone", "Tubou")
        report = TNKReport.objects.create(
            owner=user,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Jone Turaga",
            status=TNKReport.STATUS_SUBMITTED_TO_MATA,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("turani:report_edit", args=[report.pk]))

        self.assertRedirects(response, reverse("turani:report_detail", args=[report.pk]))

    def test_mata_cannot_approve_report_outside_tikina(self):
        owner = self.make_turaga("jone", "Tubou")
        mata = self.make_mata("mata", district="Moce")
        report = TNKReport.objects.create(
            owner=owner,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Jone Turaga",
            status=TNKReport.STATUS_SUBMITTED_TO_MATA,
        )
        self.client.force_login(mata)

        response = self.client.post(
            reverse("turani:report_approve", args=[report.pk]),
            {"acknowledge": "on", "comment": "Reviewed"},
        )

        self.assertEqual(response.status_code, 404)
        report.refresh_from_db()
        self.assertEqual(report.status, TNKReport.STATUS_SUBMITTED_TO_MATA)

    def test_roko_cannot_final_approve_draft_report(self):
        owner = self.make_turaga("jone", "Tubou")
        roko = get_user_model().objects.create_user("roko", password="StrongPass123!")
        Group.objects.get_or_create(name="roko_admin")[0].user_set.add(roko)
        report = TNKReport.objects.create(
            owner=owner,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Jone Turaga",
            status=TNKReport.STATUS_DRAFT,
        )
        self.client.force_login(roko)

        response = self.client.post(
            reverse("turani:report_final_approve", args=[report.pk]),
            {"acknowledge": "on", "comment": "Final approval"},
        )

        self.assertRedirects(response, reverse("turani:report_detail", args=[report.pk]))
        report.refresh_from_db()
        self.assertEqual(report.status, TNKReport.STATUS_DRAFT)

    def test_mata_approval_records_audit_action_and_escalates(self):
        owner = self.make_turaga("jone", "Tubou")
        mata = self.make_mata("mata")
        report = TNKReport.objects.create(
            owner=owner,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Jone Turaga",
            status=TNKReport.STATUS_SUBMITTED_TO_MATA,
        )
        self.client.force_login(mata)

        response = self.client.post(
            reverse("turani:report_approve", args=[report.pk]),
            {"acknowledge": "on", "comment": "Approved for Yavusa review"},
        )

        self.assertRedirects(response, reverse("turani:report_detail", args=[report.pk]))
        report.refresh_from_db()
        self.assertEqual(report.status, TNKReport.STATUS_SUBMITTED_TO_LIULIU)
        action = report.approval_actions.get(action_type=TNKApprovalAction.ACTION_APPROVE)
        self.assertEqual(action.user_full_name, "Mata Mata")
        self.assertIn("Approved for Yavusa review", action.comment)

    def test_report_exports_as_pdf(self):
        user = self.make_turaga("jone", "Tubou")
        report = TNKReport.objects.create(
            owner=user,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Jone Turaga",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("turani:report_pdf", args=[report.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

# Create your tests here.
