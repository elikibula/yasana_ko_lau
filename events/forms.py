from django import forms

from .models import Event


FIELD_CLASS = "lau-input"


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "category",
            "description",
            "location",
            "tikina",
            "cover_image",
            "start_date",
            "end_date",
            "is_all_day",
            "status",
            "is_featured",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": FIELD_CLASS}),
            "category": forms.Select(attrs={"class": FIELD_CLASS}),
            "description": forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 8}),
            "location": forms.TextInput(attrs={"class": FIELD_CLASS}),
            "tikina": forms.Select(attrs={"class": FIELD_CLASS}),
            "start_date": forms.DateTimeInput(attrs={"class": FIELD_CLASS, "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_date": forms.DateTimeInput(attrs={"class": FIELD_CLASS, "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "is_all_day": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-lau-gold text-lau-gold"}),
            "status": forms.RadioSelect(),
            "is_featured": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-lau-gold text-lau-gold"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_date"].input_formats = ["%Y-%m-%dT%H:%M"]
