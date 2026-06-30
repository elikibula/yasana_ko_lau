from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"class": "lau-input", "placeholder": "Your full name"}),
            "email": forms.EmailInput(attrs={"class": "lau-input", "placeholder": "name@example.com"}),
            "subject": forms.TextInput(attrs={"class": "lau-input", "placeholder": "How can we help?"}),
            "message": forms.Textarea(attrs={"class": "lau-input min-h-36", "placeholder": "Write your message"}),
        }
