from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from koro.models import Koro
from tikina.models import Tikina

from .models import TuragaProfile


DATE_WIDGET = forms.DateInput(attrs={"class": "form-control", "type": "date"})


class KoroSelect(forms.Select):
    """Adds the Koro's Tikina id so the profile page can filter choices client-side."""

    def __init__(self, *args, **kwargs):
        self.koro_tikina_ids = {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        tikina_id = self.koro_tikina_ids.get(str(value))
        if tikina_id:
            option["attrs"]["data-tikina"] = tikina_id
        return option


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": (
            "We could not sign you in. The username may be wrongly spelt, "
            "the account may not exist, or the password may be incorrect."
        ),
        "inactive": "This account is inactive. Please contact the Provincial Office administrator.",
    }

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "class": "login-input",
                "placeholder": "Enter your username",
            }
        )
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "login-input pr-20",
                "id": "id_password",
                "placeholder": "Enter your password",
            }
        ),
    )


class SignUpForm(UserCreationForm):
    membership_type = forms.ChoiceField(
        choices=TuragaProfile.MEMBERSHIP_TYPES[:3],
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Registering as",
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    date_of_birth = forms.DateField(widget=DATE_WIDGET, required=False)
    appointment_date = forms.DateField(widget=DATE_WIDGET, required=False, label="Date appointed (Turaga ni Koro)")
    village = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    district = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}), label="Tikina / District")
    province = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}), initial="Lau")
    phone_number = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    tokatoka = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    mataqali = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    yavusa = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    vanua = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = (
            "membership_type", "username", "email", "first_name", "last_name", "date_of_birth",
            "appointment_date", "village", "district", "province", "phone_number",
            "tokatoka", "mataqali", "yavusa", "vanua",
            "password1", "password2",
        )
        widgets = {"username": forms.TextInput(attrs={"class": "form-control"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("membership_type")
        required = {
            TuragaProfile.TURAGA_NI_KORO: ("date_of_birth", "appointment_date", "village", "district"),
            TuragaProfile.MATA_NI_TIKINA: ("date_of_birth", "village", "district"),
            TuragaProfile.TURAGA_NI_YAVUSA: ("tokatoka", "mataqali", "yavusa", "vanua"),
        }.get(role, ())
        for field in required:
            if not cleaned.get(field):
                self.add_error(field, "This field is required for the selected account type.")
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.turaga_profile
            for field in (
                "membership_type", "date_of_birth", "appointment_date", "village", "district",
                "province", "phone_number", "tokatoka", "mataqali", "yavusa", "vanua",
            ):
                setattr(profile, field, self.cleaned_data[field])
            profile.save()
        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
    district = forms.ModelChoiceField(
        queryset=Tikina.objects.none(),
        required=False,
        empty_label="Select Tikina",
        label="Tikina",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    village = forms.ModelChoiceField(
        queryset=Koro.objects.none(),
        required=False,
        empty_label="Select Koro",
        label="Koro / Village",
        widget=KoroSelect(attrs={"class": "form-select"}),
    )

    class Meta:
        model = TuragaProfile
        fields = (
            "first_name", "last_name", "email", "date_of_birth", "appointment_date",
            "village", "district", "province", "phone_number", "tokatoka", "mataqali", "yavusa", "vanua",
        )
        widgets = {
            "date_of_birth": DATE_WIDGET,
            "appointment_date": DATE_WIDGET,
            "province": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "tokatoka": forms.TextInput(attrs={"class": "form-control"}),
            "mataqali": forms.TextInput(attrs={"class": "form-control"}),
            "yavusa": forms.TextInput(attrs={"class": "form-control"}),
            "vanua": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tikina_queryset = Tikina.objects.filter(is_active=True).order_by("number")
        koro_queryset = Koro.objects.filter(tikina__is_active=True).select_related("tikina").order_by("tikina__number", "name")
        self.fields["district"].queryset = tikina_queryset
        self.fields["village"].queryset = koro_queryset
        self.fields["village"].widget.koro_tikina_ids = {
            str(koro.pk): str(koro.tikina_id) for koro in koro_queryset
        }
        self._selected_tikina = None
        self._selected_koro = None

        if self.instance and self.instance.user_id:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email
            user_profile = getattr(self.instance.user, "user_profile", None)
            saved_district = self.instance.district or (user_profile.tikina if user_profile else "")
            saved_village = self.instance.village or (user_profile.koro if user_profile else "")
            selected_tikina = self._find_tikina(tikina_queryset, saved_district)
            if selected_tikina:
                self.fields["district"].initial = selected_tikina.pk
                selected_koro = self._find_koro(koro_queryset, saved_village, selected_tikina)
                if selected_koro:
                    self.fields["village"].initial = selected_koro.pk

    @staticmethod
    def _normalise_place_name(value):
        return " ".join(str(value or "").strip().upper().split())

    def _find_tikina(self, queryset, value):
        normalised = self._normalise_place_name(value)
        if not normalised:
            return None
        return next(
            (
                tikina
                for tikina in queryset
                if self._normalise_place_name(tikina.name) == normalised
            ),
            None,
        )

    def _find_koro(self, queryset, value, tikina):
        normalised = self._normalise_place_name(value)
        if not normalised:
            return None
        return next(
            (
                koro
                for koro in queryset
                if koro.tikina_id == tikina.pk
                and self._normalise_place_name(koro.name) == normalised
            ),
            None,
        )

    def clean_district(self):
        self._selected_tikina = self.cleaned_data["district"]
        return self._selected_tikina.name if self._selected_tikina else ""

    def clean_village(self):
        self._selected_koro = self.cleaned_data["village"]
        return self._selected_koro.name if self._selected_koro else ""

    def clean(self):
        cleaned = super().clean()
        if (
            self._selected_tikina
            and self._selected_koro
            and self._selected_koro.tikina_id != self._selected_tikina.pk
        ):
            self.add_error("village", "Select a Koro that belongs to the chosen Tikina.")
        role = self.instance.membership_type
        required = {
            TuragaProfile.TURAGA_NI_KORO: ("date_of_birth", "appointment_date", "village", "district"),
            TuragaProfile.MATA_NI_TIKINA: ("date_of_birth", "village", "district"),
            TuragaProfile.TURAGA_NI_YAVUSA: ("tokatoka", "mataqali", "yavusa", "vanua"),
        }.get(role, ())
        for field in required:
            if not cleaned.get(field):
                self.add_error(field, "This field is required for your account type.")
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        profile.district = self._selected_tikina.name if self._selected_tikina else ""
        profile.village = self._selected_koro.name if self._selected_koro else ""
        if commit:
            user.save()
            profile.save()
        return profile
