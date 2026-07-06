from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import TuragaProfile
from .models import TNYReport


class YavusaReportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "yavusa",
            email="ratu@example.com",
            password="StrongPass123!",
            first_name="Ratu",
            last_name="Peni",
        )
        profile = self.user.turaga_profile
        profile.membership_type = TuragaProfile.TURAGA_NI_YAVUSA
        profile.province = "Lau"
        profile.phone_number = "9900000"
        profile.village = "Tubou"
        profile.district = "Lakeba"
        profile.tokatoka = "Vunivau"
        profile.mataqali = "Nasaqalau"
        profile.yavusa = "Vuanirewa"
        profile.vanua = "Lakeba"
        profile.save()
        self.client.force_login(self.user)

    def test_create_report_snapshots_yavusa_identity(self):
        response = self.client.post(reverse("turaga_ni_yavusa:report_create"), {
            "quarter": "Q2", "year": "2026", "bosevanua_meeting_frequency": "1", "action": "save_draft",
        })
        self.assertEqual(response.status_code, 302)
        report = TNYReport.objects.get()
        self.assertEqual(report.full_name, "Ratu Peni")
        self.assertEqual(report.phone_number, "9900000")
        self.assertEqual(report.email, "ratu@example.com")
        self.assertEqual(report.yavusa, "Vuanirewa")
        self.assertEqual(report.vanua, "Lakeba")
        self.assertEqual(report.koro, "Tubou")
        self.assertEqual(report.tikina, "Lakeba")

    def test_form_and_dashboard_render(self):
        self.assertEqual(self.client.get(reverse("turaga_ni_yavusa:report_create")).status_code, 200)
        self.assertContains(self.client.get(reverse("turaga_ni_yavusa:turaga_ni_yavusa_dashboard")), "Yavusa Governance Dashboard")

    def test_report_exports_as_pdf(self):
        report = TNYReport.objects.create(
            owner=self.user,
            quarter="Q2",
            year=2026,
            full_name="Ratu Peni",
            tokatoka="Vunivau",
            mataqali="Nasaqalau",
            yavusa="Vuanirewa",
            vanua="Lakeba",
            bosevanua_meeting_frequency="1",
            status=TNYReport.STATUS_APPROVED_BY_ROKO,
        )

        response = self.client.get(reverse("turaga_ni_yavusa:report_pdf", args=[report.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
