from django import forms
from django.forms import BaseInlineFormSet


INPUT = "w-full rounded border border-lau-navy/30 px-3 py-2 text-sm focus:ring-2 focus:ring-lau-gold focus:outline-none"
SELECT = INPUT + " bg-gray-100"
AREA = INPUT + " resize-y"
CHECKBOX = "h-4 w-4 rounded border-lau-navy/30 text-lau-gold focus:ring-lau-gold"
DATE_DISPLAY_FORMAT = "%d/%m/%Y"
DATE_INPUT_FORMATS = [DATE_DISPLAY_FORMAT, "%Y-%m-%d"]


def style_widget(field):
    widget = field.widget
    if isinstance(field, forms.DateField):
        field.input_formats = DATE_INPUT_FORMATS
        widget.format = DATE_DISPLAY_FORMAT
    if isinstance(widget, forms.CheckboxInput):
        widget.attrs.update({"class": CHECKBOX})
    elif isinstance(widget, forms.Select):
        widget.attrs.update({"class": SELECT})
    elif isinstance(widget, forms.Textarea):
        widget.attrs.update({"class": AREA, "rows": widget.attrs.get("rows", 3)})
    else:
        widget.attrs.update({"class": INPUT})
    if isinstance(field, forms.DateField):
        widget.attrs.update({"type": "text", "placeholder": "dd/mm/yyyy", "inputmode": "numeric"})


class StyledModelFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            style_widget(field)


class StyledInlineFormSet(BaseInlineFormSet):
    inline_labels = {}

    def add_fields(self, form, index):
        super().add_fields(form, index)
        labels = self.inline_labels.get(form._meta.model.__name__, {})
        for name, field in form.fields.items():
            field.label = labels.get(name, field.label)
            style_widget(field)
