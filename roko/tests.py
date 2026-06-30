from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class RokoDashboardTests(TestCase):
    def test_staff_can_view_integrated_dashboard(self):
        user = get_user_model().objects.create_user("roko", password="StrongPass123!", is_staff=True)
        self.client.force_login(user)
        response = self.client.get(reverse("roko:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vakadinadina ni iTukutuku ni Yasana")
        self.assertContains(response, "Vakadinadina Vei Ira na Vakayagataka")
        self.assertContains(response, reverse("turani:report_list"))
        self.assertContains(response, reverse("mata_ni_tikina:report_list"))
        self.assertContains(response, reverse("turaga_ni_yavusa:report_list"))
