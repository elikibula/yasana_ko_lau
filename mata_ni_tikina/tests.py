from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import TuragaProfile
from .models import MNTReport


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
        self.assertContains(self.client.get(reverse("mata_ni_tikina:mata_ni_tikina_dashboard")), "Tikina Governance Dashboard")

    def test_wrong_membership_cannot_enter_mata_area(self):
        self.user.turaga_profile.membership_type = TuragaProfile.TURAGA_NI_KORO
        self.user.turaga_profile.appointment_date = date(2020, 1, 1)
        self.user.turaga_profile.save()
        response = self.client.get(reverse("mata_ni_tikina:mata_ni_tikina_dashboard"))
        self.assertRedirects(response, reverse("accounts:dashboard"), fetch_redirect_response=False)
