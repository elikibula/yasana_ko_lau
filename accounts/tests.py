from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from koro.models import Koro
from tikina.models import Tikina


class AccountFlowTests(TestCase):
    def test_profile_uses_tikina_and_dependent_koro_dropdowns(self):
        tikina = Tikina.objects.create(number=1, name="LAKEBA", koro_turaga="TUBOU")
        other_tikina = Tikina.objects.create(number=2, name="MOCE", koro_turaga="MOCE")
        koro = Koro.objects.create(name="TUBOU", tikina=tikina, is_koro_turaga=True)
        other_koro = Koro.objects.create(name="MOCE", tikina=other_tikina, is_koro_turaga=True)
        user = get_user_model().objects.create_user("profile-user", password="StrongPass123!")
        profile = user.turaga_profile
        profile.membership_type = "turaga_ni_koro"
        profile.province = "Lau"
        profile.save()
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertContains(response, f'value="{tikina.pk}"')
        self.assertContains(response, f'value="{koro.pk}"')
        self.assertContains(response, f'data-tikina="{tikina.pk}"')

        response = self.client.post(reverse("accounts:profile"), {
            "first_name": "Jone", "last_name": "Vulaono", "email": "jone@example.com",
            "date_of_birth": "1980-04-12", "appointment_date": "2023-01-15",
            "district": tikina.pk, "village": koro.pk, "province": "Lau", "phone_number": "9900000",
        })

        self.assertRedirects(response, reverse("accounts:dashboard"), fetch_redirect_response=False)
        profile.refresh_from_db()
        self.assertEqual(profile.district, "LAKEBA")
        self.assertEqual(profile.village, "TUBOU")
        self.assertEqual(user.user_profile.tikina, "LAKEBA")
        self.assertEqual(user.user_profile.koro, "TUBOU")
        koro.refresh_from_db()
        self.assertEqual(koro.turaga_ni_koro, user.user_profile)

        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.context["form"].fields["district"].initial, tikina.pk)
        self.assertEqual(response.context["form"].fields["village"].initial, koro.pk)

        response = self.client.post(reverse("accounts:profile"), {
            "first_name": "Jone", "last_name": "Vulaono", "email": "jone@example.com",
            "date_of_birth": "1980-04-12", "appointment_date": "2023-01-15",
            "district": tikina.pk, "village": other_koro.pk, "province": "Lau", "phone_number": "9900000",
        })
        self.assertContains(response, "Select a Koro that belongs to the chosen Tikina.")

    def test_registration_captures_required_turaga_details_and_logs_user_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "jone",
                "membership_type": "turaga_ni_koro",
                "email": "jone@example.com",
                "first_name": "Jone",
                "last_name": "Vulaono",
                "date_of_birth": "1980-04-12",
                "appointment_date": "2023-01-15",
                "village": "Tubou",
                "district": "Lakeba",
                "province": "Lau",
                "phone_number": "9900000",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("accounts:dashboard"), fetch_redirect_response=False)
        user = get_user_model().objects.get(username="jone")
        self.assertEqual(user.first_name, "Jone")
        self.assertEqual(user.turaga_profile.village, "Tubou")
        self.assertEqual(user.turaga_profile.date_of_birth, date(1980, 4, 12))
        self.assertTrue(user.turaga_profile.is_complete)
        self.assertEqual(user.turaga_profile.membership_type, "turaga_ni_koro")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_incomplete_existing_account_is_sent_to_profile(self):
        user = get_user_model().objects.create_user("legacy", password="StrongPass123!")
        self.client.force_login(user)

        response = self.client.get(reverse("turani:report_list"))

        self.assertRedirects(response, reverse("accounts:profile"))

    def test_yavusa_registration_requires_and_saves_vanua_identity(self):
        response = self.client.post(reverse("accounts:signup"), {
            "membership_type": "turaga_ni_yavusa", "username": "ratu", "email": "ratu@example.com",
            "first_name": "Ratu", "last_name": "Savenaca", "province": "Lau", "tokatoka": "Vunivau",
            "mataqali": "Nasaqalau", "yavusa": "Vuanirewa", "vanua": "Lakeba",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 302)
        profile = get_user_model().objects.get(username="ratu").turaga_profile
        self.assertEqual(profile.membership_type, "turaga_ni_yavusa")
        self.assertEqual(profile.yavusa, "Vuanirewa")
        self.assertTrue(profile.is_complete)


class NavigationTests(TestCase):
    def make_member(self, username, role):
        user = get_user_model().objects.create_user(username, password="StrongPass123!", first_name="Menu", last_name="Tester")
        profile = user.turaga_profile
        profile.membership_type = role
        profile.province = "Lau"
        if role == "turaga_ni_koro":
            profile.date_of_birth = date(1980, 1, 1)
            profile.appointment_date = date(2020, 1, 1)
            profile.village = "Tubou"
            profile.district = "Lakeba"
        elif role == "mata_ni_tikina":
            profile.date_of_birth = date(1980, 1, 1)
            profile.village = "Tubou"
            profile.district = "Lakeba"
        else:
            profile.tokatoka = "Vunivau"
            profile.mataqali = "Nasaqalau"
            profile.yavusa = "Vuanirewa"
            profile.vanua = "Lakeba"
        profile.save()
        return user

    def test_each_role_dashboard_renders_its_own_menu(self):
        cases = (
            ("turaga_ni_koro", "turani:turaga_dashboard", "turani:report_create"),
            ("mata_ni_tikina", "mata_ni_tikina:mata_ni_tikina_dashboard", "mata_ni_tikina:report_create"),
            ("turaga_ni_yavusa", "turaga_ni_yavusa:turaga_ni_yavusa_dashboard", "turaga_ni_yavusa:report_create"),
        )
        for index, (role, dashboard_name, create_name) in enumerate(cases):
            user = self.make_member(f"menu{index}", role)
            self.client.force_login(user)
            response = self.client.get(reverse(dashboard_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, reverse(create_name))
            self.assertContains(response, reverse("accounts:profile"))
            self.client.logout()
