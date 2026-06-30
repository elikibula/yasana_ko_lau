from pathlib import Path

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class DocumentCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class, e.g. 'fa-file-pdf'")

    class Meta:
        verbose_name_plural = "Document Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    ACCESS_CHOICES = [
        ("public", "Public - Anyone can download"),
        ("login", "Login Required - Any authenticated user"),
        ("koro", "Turaga ni Koro and above"),
        ("tikina", "Mata ni Tikina and above"),
        ("admin", "Roko Admin only"),
    ]

    FILE_TYPE_CHOICES = [
        ("pdf", "PDF Document"),
        ("docx", "Word Document"),
        ("xlsx", "Excel Spreadsheet"),
        ("pptx", "PowerPoint Presentation"),
        ("image", "Image"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="documents/%Y/%m/")
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default="pdf")
    file_size_kb = models.PositiveIntegerField(default=0, editable=False, help_text="Auto-calculated on save")
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default="public")
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags, e.g. minutes, 2024, Lakeba")
    year = models.PositiveIntegerField(null=True, blank=True, help_text="Document year for filtering")
    version = models.CharField(max_length=20, blank=True, help_text="e.g. v1.0, Rev 2")
    is_featured = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0, editable=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="documents_uploaded")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("documents:detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.file:
            self.file_size_kb = self.file.size // 1024
            if not self.file_type:
                self.file_type = detect_file_type(self.file.name)
        super().save(*args, **kwargs)

    def get_file_size_display(self):
        if self.file_size_kb < 1024:
            return f"{self.file_size_kb} KB"
        return f"{self.file_size_kb / 1024:.1f} MB"


def detect_file_type(filename):
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix in {"pdf", "docx", "xlsx", "pptx"}:
        return suffix
    if suffix in {"jpg", "jpeg", "png", "gif", "webp"}:
        return "image"
    return "other"
