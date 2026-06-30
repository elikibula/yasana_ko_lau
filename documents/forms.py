from django import forms

from .models import Document, detect_file_type


FIELD_CLASS = "lau-input"


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            "title",
            "category",
            "description",
            "file",
            "file_type",
            "access_level",
            "tags",
            "year",
            "version",
            "is_featured",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": FIELD_CLASS}),
            "category": forms.Select(attrs={"class": FIELD_CLASS}),
            "description": forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 5}),
            "file": forms.ClearableFileInput(attrs={"class": FIELD_CLASS}),
            "file_type": forms.Select(attrs={"class": FIELD_CLASS}),
            "access_level": forms.RadioSelect(),
            "tags": forms.TextInput(attrs={"class": FIELD_CLASS}),
            "year": forms.NumberInput(attrs={"class": FIELD_CLASS}),
            "version": forms.TextInput(attrs={"class": FIELD_CLASS}),
            "is_featured": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-lau-gold text-lau-gold"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.file and "file" in self.changed_data:
            instance.file_type = instance.file_type or detect_file_type(instance.file.name)
            detected_type = detect_file_type(instance.file.name)
            if detected_type != "other":
                instance.file_type = detected_type
        if commit:
            instance.save()
            self.save_m2m()
        return instance
