from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import TuragaProfile, UserProfile
from common.reporting_periods import is_report_overdue, reporting_due_date
from koro.models import Koro
from tikina.models import Tikina
from turani.models import TNKReport


class AdminDashboardTests(TestCase):
    def make_admin(self):
        admin = get_user_model().objects.create_user("admin", password="StrongPass123!")
        group, _ = Group.objects.get_or_create(name="roko_admin")
        admin.groups.add(group)
        return admin

    def test_dashboard_shows_pdf_export_links(self):
        admin = self.make_admin()
        owner = get_user_model().objects.create_user("owner", password="StrongPass123!")
        report = TNKReport.objects.create(
            owner=owner,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Owner Turaga",
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Report PDF exports")
        self.assertContains(response, reverse("turani:report_pdf", args=[report.pk]))

    def test_reporting_due_dates_use_requested_timelines(self):
        self.assertEqual(reporting_due_date("Q1", 2026), date(2026, 4, 30))
        self.assertEqual(reporting_due_date("Q2", 2026), date(2026, 7, 31))
        self.assertEqual(reporting_due_date("Q3", 2026), date(2026, 10, 31))
        self.assertEqual(reporting_due_date("Q4", 2026), date(2027, 1, 31))

    def test_draft_report_is_overdue_after_due_date(self):
        owner = get_user_model().objects.create_user("deadline-owner", password="StrongPass123!")
        report = TNKReport.objects.create(
            owner=owner,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Owner Turaga",
        )

        self.assertTrue(is_report_overdue(report, today=date(2026, 5, 1)))

        report.status = TNKReport.STATUS_SUBMITTED
        self.assertFalse(is_report_overdue(report, today=date(2026, 5, 1)))

    def test_dashboard_counts_overdue_pdf_reports(self):
        admin = self.make_admin()
        owner = get_user_model().objects.create_user("overdue-owner", password="StrongPass123!")
        TNKReport.objects.create(
            owner=owner,
            quarter="Q1",
            year=2000,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Owner Turaga",
        )
        TNKReport.objects.create(
            owner=owner,
            quarter="Q2",
            year=2000,
            village="Nukunuku",
            district="Lakeba",
            province="Lau",
            village_headman_name="Owner Turaga",
            status=TNKReport.STATUS_SUBMITTED,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertEqual(response.context["overdue_count"], 1)

    def test_user_management_link_uses_frontend_pages(self):
        admin = self.make_admin()
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertContains(response, reverse("admin_panel:user_list"))
        self.assertNotContains(response, reverse("admin:auth_user_changelist"))

    def test_roko_admin_can_create_mata_ni_tikina_user(self):
        admin = self.make_admin()
        tikina = Tikina.objects.create(number=1, name="Lakeba")
        koro = Koro.objects.create(name="Tubou", tikina=tikina)
        self.client.force_login(admin)

        response = self.client.post(
            reverse("admin_panel:user_create"),
            {
                "role": UserProfile.MATA_NI_TIKINA,
                "username": "mata-user",
                "first_name": "Josaia",
                "last_name": "Tawake",
                "email": "mata@example.com",
                "is_active": "on",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "date_of_birth": "1980-01-02",
                "village": koro.pk,
                "district": tikina.pk,
                "province": "Lau",
                "phone_number": "9900000",
            },
        )

        self.assertRedirects(response, reverse("admin_panel:user_list"))
        user = get_user_model().objects.get(username="mata-user")
        self.assertTrue(user.groups.filter(name=UserProfile.MATA_NI_TIKINA).exists())
        self.assertEqual(user.turaga_profile.membership_type, TuragaProfile.MATA_NI_TIKINA)
        self.assertEqual(user.turaga_profile.date_of_birth, date(1980, 1, 2))
        self.assertEqual(user.user_profile.role, UserProfile.MATA_NI_TIKINA)
        self.assertEqual(user.user_profile.tikina, "LAKEBA")

    def test_user_form_filters_koro_by_tikina(self):
        admin = self.make_admin()
        tikina = Tikina.objects.create(number=1, name="Lakeba")
        other_tikina = Tikina.objects.create(number=2, name="Moce")
        koro = Koro.objects.create(name="Tubou", tikina=tikina)
        Koro.objects.create(name="Naroi", tikina=other_tikina)
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_panel:user_create"))

        self.assertContains(response, f'value="{tikina.pk}"')
        self.assertContains(response, f'value="{koro.pk}"')
        self.assertContains(response, f'data-tikina="{tikina.pk}"')

    def test_user_form_rejects_koro_outside_selected_tikina(self):
        admin = self.make_admin()
        tikina = Tikina.objects.create(number=1, name="Lakeba")
        other_tikina = Tikina.objects.create(number=2, name="Moce")
        wrong_koro = Koro.objects.create(name="Naroi", tikina=other_tikina)
        self.client.force_login(admin)

        response = self.client.post(
            reverse("admin_panel:user_create"),
            {
                "role": UserProfile.MATA_NI_TIKINA,
                "username": "bad-area",
                "first_name": "Bad",
                "last_name": "Area",
                "email": "bad@example.com",
                "is_active": "on",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "date_of_birth": "1980-01-02",
                "village": wrong_koro.pk,
                "district": tikina.pk,
                "province": "Lau",
            },
        )

        self.assertContains(response, "Select a Koro that belongs to the chosen Tikina.")

    def test_user_management_pages_render(self):
        admin = self.make_admin()
        target = get_user_model().objects.create_user("render-target", password="StrongPass123!")
        self.client.force_login(admin)

        urls = (
            reverse("admin_panel:user_list"),
            reverse("admin_panel:user_create"),
            reverse("admin_panel:user_edit", args=[target.pk]),
            reverse("admin_panel:user_reset_password", args=[target.pk]),
            reverse("admin_panel:user_delete", args=[target.pk]),
        )
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_user_list_shows_reset_password_action(self):
        admin = self.make_admin()
        target = get_user_model().objects.create_user("reset-target", password="OldPass123!", first_name="Reset", last_name="Target")
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_panel:user_list"))

        self.assertContains(response, "Reset Password")
        self.assertContains(response, reverse("admin_panel:user_reset_password", args=[target.pk]))

    def test_roko_admin_can_reset_user_password(self):
        admin = self.make_admin()
        target = get_user_model().objects.create_user("password-target", password="OldPass123!")
        self.client.force_login(admin)

        response = self.client.post(
            reverse("admin_panel:user_reset_password", args=[target.pk]),
            {"password1": "NewStrongPass123!", "password2": "NewStrongPass123!"},
        )

        self.assertRedirects(response, reverse("admin_panel:user_list"))
        target.refresh_from_db()
        self.assertTrue(target.check_password("NewStrongPass123!"))

    def test_roko_admin_can_edit_user_role_to_roko_admin(self):
        admin = self.make_admin()
        target = get_user_model().objects.create_user("target", password="StrongPass123!", first_name="Target", last_name="User")
        self.client.force_login(admin)

        response = self.client.post(
            reverse("admin_panel:user_edit", args=[target.pk]),
            {
                "role": UserProfile.ROKO_ADMIN,
                "username": "target",
                "first_name": "Target",
                "last_name": "User",
                "email": "target@example.com",
                "is_active": "on",
                "password1": "",
                "password2": "",
                "province": "Lau",
                "phone_number": "9900001",
            },
        )

        self.assertRedirects(response, reverse("admin_panel:user_list"))
        target.refresh_from_db()
        self.assertTrue(target.groups.filter(name=UserProfile.ROKO_ADMIN).exists())
        self.assertEqual(target.turaga_profile.membership_type, TuragaProfile.ROKO)
        self.assertEqual(target.user_profile.role, UserProfile.ROKO_ADMIN)

    def test_delete_deactivates_user_when_reports_are_protected(self):
        admin = self.make_admin()
        owner = get_user_model().objects.create_user("report-owner", password="StrongPass123!")
        TNKReport.objects.create(
            owner=owner,
            quarter="Q1",
            year=2026,
            village="Tubou",
            district="Lakeba",
            province="Lau",
            village_headman_name="Owner Turaga",
        )
        self.client.force_login(admin)

        response = self.client.post(reverse("admin_panel:user_delete", args=[owner.pk]))

        self.assertRedirects(response, reverse("admin_panel:user_list"))
        owner.refresh_from_db()
        self.assertFalse(owner.is_active)
