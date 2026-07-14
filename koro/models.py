from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify


TIKINA_CHOICES = (
    ("lakeba", "Lakeba"),
    ("nayau", "Nayau"),
    ("oneata", "Oneata"),
    ("moce", "Moce"),
    ("kabara", "Kabara"),
    ("fulaga", "Fulaga"),
    ("ono_i_lau", "Ono-i-Lau"),
    ("lomaloma", "Lomaloma"),
    ("mualevu", "Mualevu"),
    ("cicia", "Cicia"),
    ("moala", "Moala"),
    ("matuku", "Matuku"),
    ("totoya", "Totoya"),
)


class Koro(models.Model):
    """
    Represents a single village in the Lau Group.
    Official names are stored uppercase to match the source register.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    tikina = models.ForeignKey("tikina.Tikina", on_delete=models.PROTECT, related_name="koro")
    is_koro_turaga = models.BooleanField(
        default=False,
        help_text="True if this village is the Koro Turaga (principal village) of its Tikina",
    )
    population = models.PositiveIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="koro/covers/", blank=True, null=True)
    turaga_ni_koro = models.OneToOneField(
        "accounts.UserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="koro_managed",
        help_text="The Turaga ni Koro user assigned to this village",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tikina__number", "-is_koro_turaga", "name"]
        verbose_name = "Koro"
        verbose_name_plural = "Koro"
        constraints = [
            models.UniqueConstraint(fields=["name", "tikina"], name="unique_koro_name_per_tikina"),
            models.UniqueConstraint(
                fields=["tikina"],
                condition=Q(is_koro_turaga=True),
                name="unique_koro_turaga_per_tikina",
            ),
        ]

    def __str__(self):
        flag = " *" if self.is_koro_turaga else ""
        return f"{self.name} ({self.tikina.name}){flag}"

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        if not self.slug:
            self.slug = f"{self.tikina.slug}-{slugify(self.name)}"
        super().save(*args, **kwargs)


class KoroDroneVideo(models.Model):
    koro = models.ForeignKey("Koro", related_name="drone_videos", on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    video_file = models.FileField(upload_to="drone_videos/%Y/%m/", blank=True, null=True)
    video_url = models.URLField(blank=True)
    thumbnail = models.ImageField(upload_to="drone_videos/thumbnails/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-uploaded_at"]

    def clean(self):
        super().clean()
        if not self.video_file and not self.video_url:
            raise ValidationError("Add either a video file or a video URL.")

    def __str__(self):
        return self.title or f"Drone video for {self.koro}"


LEGACY_TIKINA_CHOICES = (
    ("Lakeba", "Lakeba"),
    ("Oneata", "Oneata"),
    ("Moce", "Moce"),
    ("Kabara", "Kabara"),
    ("Fulaga", "Fulaga"),
    ("Ogea", "Ogea"),
    ("Vatoa", "Vatoa"),
    ("Ono-i-Lau", "Ono-i-Lau"),
    ("Cicia", "Cicia"),
    ("Nayau", "Nayau"),
    ("Vanuabalavu", "Vanuabalavu"),
    ("Mago", "Mago"),
)


class KoroReport(models.Model):
    REPORT_TYPES = (
        ("weekly", "Weekly Report"),
        ("population", "Population Update"),
        ("infrastructure", "Infrastructure Report"),
    )
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    koro_name = models.CharField(max_length=100)
    tikina = models.ForeignKey("tikina.Tikina", on_delete=models.PROTECT, related_name="koro_reports", null=True, blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.koro_name} - {self.get_report_type_display()}"
