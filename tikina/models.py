from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Tikina(models.Model):
    """
    Represents one of the 13 official Tikina of Yasana ko Lau.
    Official names are stored uppercase to match the source register.
    """

    number = models.PositiveSmallIntegerField(unique=True, help_text="Official order number (1-13)")
    name = models.CharField(max_length=100, unique=True, help_text="Official Fijian name in UPPERCASE")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    koro_turaga = models.CharField(max_length=100, help_text="Principal village / seat of the Tikina")
    official_koro_count = models.PositiveSmallIntegerField(default=0)
    island_group = models.CharField(max_length=100, blank=True)
    population = models.PositiveIntegerField(default=0)
    mataqali_count = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="tikina/covers/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    mata_ni_tikina = models.OneToOneField(
        "accounts.UserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tikina_managed",
        help_text="The Mata ni Tikina user assigned to this Tikina",
    )

    class Meta:
        ordering = ["number"]
        verbose_name = "Tikina"
        verbose_name_plural = "Tikina"

    def __str__(self):
        return f"{self.number}. {self.name}"

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        self.koro_turaga = self.koro_turaga.upper()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def koro_count(self):
        return self.koro.count()

    @property
    def koro_turaga_village(self):
        return self.koro.filter(is_koro_turaga=True).first()


class TikinaGalleryImage(models.Model):
    tikina = models.ForeignKey(Tikina, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ImageField(upload_to="tikina/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or f"{self.tikina.name} gallery image"


class TikinaReport(models.Model):
    REPORT_TYPES = (
        ("general", "General Report"),
        ("population", "Population Update"),
        ("infrastructure", "Infrastructure Report"),
    )
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tikina = models.ForeignKey(Tikina, on_delete=models.PROTECT, related_name="reports", null=True, blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default="general")
    summary = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        tikina_name = self.tikina.name if self.tikina else "Unassigned"
        return f"{tikina_name} Tikina Report"
