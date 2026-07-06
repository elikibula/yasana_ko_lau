from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from turani.models import TNKReport


class RokoDashboardTests(TestCase):
    def test_recent_reports_include_pdf_export_link(self):
        roko = get_user_model().objects.create_user("roko", password="StrongPass123!")
        group, _ = Group.objects.get_or_create(name="roko_admin")
        roko.groups.add(group)
        owner = get_user_model().objects.create_user("owner", password="StrongPass123!")
        TNKReport.objects.create(
            owner=owner,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Owner Turaga",
        )
        self.client.force_login(roko)

        response = self.client.get(reverse("roko:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("turani:report_pdf", args=[TNKReport.objects.get().pk]))
