from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from urllib.parse import parse_qs, urlparse
import re


YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def youtube_video_id(url):
    """Return a validated YouTube ID for supported URL formats, or None."""
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    candidate = None
    if host in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        parts = parsed.path.strip("/").split("/")
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [None])[0]
        elif len(parts) >= 2 and parts[0] in {"embed", "shorts"}:
            candidate = parts[1]
    return candidate if candidate and YOUTUBE_ID_RE.fullmatch(candidate) else None


def validate_video_upload(upload):
    allowed_extensions = {"mp4", "webm", "mov"}
    extension = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
    if extension not in allowed_extensions:
        raise ValidationError("Upload an MP4, WebM, or MOV video file.")
    content_type = getattr(upload, "content_type", "")
    if content_type and content_type not in {"video/mp4", "video/webm", "video/quicktime"}:
        raise ValidationError("The uploaded file does not have a supported video content type.")
    position = upload.tell()
    header = upload.read(16)
    upload.seek(position)
    looks_like_video = (extension in {"mp4", "mov"} and b"ftyp" in header) or (extension == "webm" and header.startswith(b"\x1a\x45\xdf\xa3"))
    if not looks_like_video:
        raise ValidationError("The uploaded file content does not match a supported video format.")
    max_size = getattr(settings, "NEWS_MAX_VIDEO_UPLOAD_SIZE", settings.DATA_UPLOAD_MAX_MEMORY_SIZE)
    if upload.size > max_size:
        raise ValidationError(f"Video files must be no larger than {max_size // (1024 * 1024)} MB.")


def validate_gallery_image(upload):
    extension = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
    if extension not in {"jpg", "jpeg", "png", "webp"}:
        raise ValidationError("Upload a JPG, PNG, or WebP image (SVG is not supported).")
    content_type = getattr(upload, "content_type", "")
    if content_type and content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValidationError("The uploaded file does not have a supported image content type.")
    max_size = getattr(settings, "NEWS_MAX_IMAGE_UPLOAD_SIZE", 10 * 1024 * 1024)
    if upload.size > max_size:
        raise ValidationError(f"Images must be no larger than {max_size // (1024 * 1024)} MB.")


class NewsCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "News Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class NewsPost(models.Model):
    NEWS_TYPE_ARTICLE = "article"
    NEWS_TYPE_PHOTO = "photo"
    NEWS_TYPE_VIDEO = "video"
    NEWS_TYPE_CHOICES = (
        (NEWS_TYPE_ARTICLE, "Article News"),
        (NEWS_TYPE_PHOTO, "Photo News"),
        (NEWS_TYPE_VIDEO, "Video News"),
    )
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=200)
    news_type = models.CharField(max_length=20, choices=NEWS_TYPE_CHOICES, default=NEWS_TYPE_ARTICLE)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(
        NewsCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="news_posts")
    cover_image = models.ImageField(upload_to="news/covers/", blank=True, null=True)
    summary = models.TextField(max_length=300, help_text="Short summary shown on listing cards (max 300 chars)")
    body = models.TextField(blank=True, help_text="Full article body. Supports basic HTML.")
    video_file = models.FileField(upload_to="news/videos/%Y/%m/", blank=True, null=True, validators=[validate_video_upload])
    video_url = models.URLField(blank=True, help_text="Paste a YouTube or supported external video URL.")
    video_thumbnail = models.ImageField(upload_to="news/video-thumbnails/%Y/%m/", blank=True, null=True, validators=[validate_gallery_image])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_featured = models.BooleanField(default=False, help_text="Pin to top of homepage news section")
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news:detail", kwargs={"slug": self.slug})

    def clean(self):
        super().clean()
        if self.news_type == self.NEWS_TYPE_ARTICLE and not self.body.strip():
            raise ValidationError({"body": "Article News requires an article body."})
        if self.news_type == self.NEWS_TYPE_VIDEO and not self.video_file and not self.video_url:
            raise ValidationError("Video News requires either an uploaded video or a video URL.")
        if self.video_url and "youtu" in self.video_url.lower() and not youtube_video_id(self.video_url):
            raise ValidationError({"video_url": "Enter a supported, valid YouTube video URL."})

    @property
    def is_article_news(self):
        return self.news_type == self.NEWS_TYPE_ARTICLE

    @property
    def is_photo_news(self):
        return self.news_type == self.NEWS_TYPE_PHOTO

    @property
    def is_video_news(self):
        return self.news_type == self.NEWS_TYPE_VIDEO

    @property
    def youtube_embed_url(self):
        video_id = youtube_video_id(self.video_url)
        return f"https://www.youtube.com/embed/{video_id}" if video_id else ""

    @property
    def card_image(self):
        if self.video_thumbnail:
            return self.video_thumbnail
        if self.cover_image:
            return self.cover_image
        first_photo = next(iter(self.photos.all()), None)
        return first_photo.image if first_photo else None

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class NewsPhoto(models.Model):
    news = models.ForeignKey(NewsPost, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="news/photos/%Y/%m/", validators=[validate_gallery_image])
    caption = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.caption or f"Photo for {self.news.title}"
