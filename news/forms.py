from django import forms
from django.utils import timezone

from .models import NewsPhoto, NewsPost, youtube_video_id


FIELD_CLASS = "lau-input"


class NewsPostForm(forms.ModelForm):
    class Meta:
        model = NewsPost
        fields = ["title", "news_type", "category", "cover_image", "summary", "body", "video_file", "video_url", "video_thumbnail", "status", "is_featured"]
        widgets = {
            "title": forms.TextInput(attrs={"class": FIELD_CLASS}),
            "news_type": forms.Select(attrs={"class": FIELD_CLASS, "data-news-type": "true"}),
            "category": forms.Select(attrs={"class": FIELD_CLASS}),
            "summary": forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 3, "maxlength": 300}),
            "body": forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 12}),
            "video_url": forms.URLInput(attrs={"class": FIELD_CLASS, "placeholder": "https://www.youtube.com/watch?v=..."}),
            "status": forms.RadioSelect(),
            "is_featured": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-lau-gold text-lau-gold"}),
        }

    def clean(self):
        cleaned = super().clean()
        news_type = cleaned.get("news_type")
        if news_type == NewsPost.NEWS_TYPE_ARTICLE and not cleaned.get("body", "").strip():
            self.add_error("body", "Article News requires an article body.")
        if news_type == NewsPost.NEWS_TYPE_VIDEO:
            if not cleaned.get("video_file") and not cleaned.get("video_url"):
                raise forms.ValidationError("Video News requires either an uploaded video or a video URL.")
            url = cleaned.get("video_url")
            if url and "youtu" in url.lower() and not youtube_video_id(url):
                self.add_error("video_url", "Enter a supported, valid YouTube video URL.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.status == "published" and not instance.published_at:
            instance.published_at = timezone.now()
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class NewsPhotoForm(forms.ModelForm):
    class Meta:
        model = NewsPhoto
        fields = ["image", "caption", "display_order"]
        widgets = {
            "caption": forms.TextInput(attrs={"class": FIELD_CLASS}),
            "display_order": forms.NumberInput(attrs={"class": FIELD_CLASS, "min": 0}),
        }


NewsPhotoFormSet = forms.inlineformset_factory(
    NewsPost, NewsPhoto, form=NewsPhotoForm, extra=1, can_delete=True, min_num=0, validate_min=False
)
