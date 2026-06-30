from datetime import date

from django.conf import settings
from django.db import models


class TuragaProfile(models.Model):
    TURAGA_NI_KORO = "turaga_ni_koro"
    MATA_NI_TIKINA = "mata_ni_tikina"
    TURAGA_NI_YAVUSA = "turaga_ni_yavusa"
    ROKO = "roko"
    MEMBERSHIP_TYPES = (
        (TURAGA_NI_KORO, "Turaga ni Koro"),
        (MATA_NI_TIKINA, "Mata ni Tikina"),
        (TURAGA_NI_YAVUSA, "Turaga ni Yavusa"),
        (ROKO, "Roko / Provincial Staff"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="turaga_profile",
    )
    membership_type = models.CharField(
        max_length=30,
        choices=MEMBERSHIP_TYPES,
        default=TURAGA_NI_KORO,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    appointment_date = models.DateField(null=True, blank=True)
    village = models.CharField(max_length=150, blank=True)
    district = models.CharField(max_length=150, blank=True)
    province = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    tokatoka = models.CharField(max_length=150, blank=True)
    mataqali = models.CharField(max_length=150, blank=True)
    yavusa = models.CharField(max_length=150, blank=True)
    vanua = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return self.user.get_full_name().strip() or self.user.username

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_complete(self):
        common = [self.user.first_name, self.user.last_name, self.province]
        if self.membership_type == self.TURAGA_NI_KORO:
            required = [self.date_of_birth, self.appointment_date, self.village, self.district]
        elif self.membership_type == self.MATA_NI_TIKINA:
            required = [self.date_of_birth, self.village, self.district]
        elif self.membership_type == self.TURAGA_NI_YAVUSA:
            required = [self.tokatoka, self.mataqali, self.yavusa, self.vanua]
        else:
            required = []
        return all(common + required)

    @property
    def dashboard_url_name(self):
        return {
            self.TURAGA_NI_KORO: "turani:turaga_dashboard",
            self.MATA_NI_TIKINA: "mata_ni_tikina:mata_ni_tikina_dashboard",
            self.TURAGA_NI_YAVUSA: "turaga_ni_yavusa:turaga_ni_yavusa_dashboard",
            self.ROKO: "roko:dashboard",
        }.get(self.membership_type, "accounts:profile")

    def __str__(self):
        return f"{self.full_name} - {self.village or 'Profile incomplete'}"


class UserProfile(models.Model):
    TURAGA_NI_KORO = "turaga_ni_koro"
    MATA_NI_TIKINA = "mata_ni_tikina"
    LIULIU_NI_YAVUSA = "liuliu_ni_yavusa"
    ROKO_ADMIN = "roko_admin"
    ROLE_CHOICES = (
        (TURAGA_NI_KORO, "Turaga ni Koro"),
        (MATA_NI_TIKINA, "Mata ni Tikina"),
        (LIULIU_NI_YAVUSA, "Liuliu ni Yavusa"),
        (ROKO_ADMIN, "Roko Admin"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_profile",
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, blank=True)
    tikina = models.CharField(max_length=100, blank=True)
    koro = models.CharField(max_length=100, blank=True)
    yavusa = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    @property
    def display_role(self):
        return self.get_role_display() if self.role else "Role pending"

    def __str__(self):
        return f"{self.user.get_username()} - {self.display_role}"
