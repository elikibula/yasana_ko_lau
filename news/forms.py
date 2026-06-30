from django import forms
from django.utils import timezone

from .models import NewsPost


FIELD_CLASS = "lau-input"


class NewsPostForm(forms.ModelForm):
    class Meta:
        model = NewsPost
        fields = ["title", "category", "cover_image", "summary", "body", "status", "is_featured"]
        widgets = {
            "title": forms.TextInput(attrs={"class": FIELD_CLASS}),
            "category": forms.Select(attrs={"class": FIELD_CLASS}),
            "summary": forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 3, "maxlength": 300}),
            "body": forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 12}),
            "status": forms.RadioSelect(),
            "is_featured": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-lau-gold text-lau-gold"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.status == "published" and not instance.published_at:
            instance.published_at = timezone.now()
        if commit:
            instance.save()
            self.save_m2m()
        return instance
