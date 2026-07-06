from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import TuragaProfile, UserProfile
from accounts.views import sync_user_role
from koro.models import Koro
from tikina.models import Tikina


INPUT = "lau-input w-full"
DATE_INPUT = forms.DateInput(format="%Y-%m-%d", attrs={"class": INPUT, "type": "date"})

ROLE_CHOICES = (
    (UserProfile.TURAGA_NI_KORO, "Turaga ni Koro"),
    (UserProfile.MATA_NI_TIKINA, "Mata ni Tikina"),
    (UserProfile.LIULIU_NI_YAVUSA, "Liuliu ni Yavusa"),
    (UserProfile.ROKO_ADMIN, "Roko Admin"),
)

ROLE_TO_MEMBERSHIP = {
    UserProfile.TURAGA_NI_KORO: TuragaProfile.TURAGA_NI_KORO,
    UserProfile.MATA_NI_TIKINA: TuragaProfile.MATA_NI_TIKINA,
    UserProfile.LIULIU_NI_YAVUSA: TuragaProfile.TURAGA_NI_YAVUSA,
    UserProfile.ROKO_ADMIN: TuragaProfile.ROKO,
}


def _field(widget=None, **kwargs):
    attrs = {"class": INPUT}
    if widget:
        widget.attrs.update(attrs)
        return widget
    return forms.TextInput(attrs=attrs)


class KoroSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        self.koro_tikina_ids = {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        tikina_id = self.koro_tikina_ids.get(str(value))
        if tikina_id:
            option["attrs"]["data-tikina"] = tikina_id
        return option


class ManagedUserForm(forms.Form):
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": INPUT}))
    username = forms.CharField(max_length=150, widget=_field())
    first_name = forms.CharField(max_length=150, widget=_field())
    last_name = forms.CharField(max_length=150, widget=_field())
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": INPUT}))
    is_active = forms.BooleanField(required=False, initial=True)
    password1 = forms.CharField(required=False, strip=False, widget=forms.PasswordInput(attrs={"class": INPUT}))
    password2 = forms.CharField(required=False, strip=False, widget=forms.PasswordInput(attrs={"class": INPUT}))
    date_of_birth = forms.DateField(required=False, widget=DATE_INPUT)
    appointment_date = forms.DateField(required=False, widget=DATE_INPUT)
    district = forms.ModelChoiceField(
        queryset=Tikina.objects.none(),
        required=False,
        empty_label="Select Tikina",
        label="Tikina / District",
        widget=forms.Select(attrs={"class": INPUT}),
    )
    village = forms.ModelChoiceField(
        queryset=Koro.objects.none(),
        required=False,
        empty_label="Select Koro",
        label="Koro / Village",
        widget=KoroSelect(attrs={"class": INPUT}),
    )
    province = forms.CharField(max_length=150, required=False, initial="Lau", widget=_field())
    phone_number = forms.CharField(max_length=30, required=False, widget=_field())
    tokatoka = forms.CharField(max_length=150, required=False, widget=_field())
    mataqali = forms.CharField(max_length=150, required=False, widget=_field())
    yavusa = forms.CharField(max_length=150, required=False, widget=_field())
    vanua = forms.CharField(max_length=150, required=False, widget=_field())

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        tikina_queryset = Tikina.objects.filter(is_active=True).order_by("number", "name")
        koro_queryset = Koro.objects.filter(tikina__is_active=True).select_related("tikina").order_by("tikina__number", "name")
        self.fields["district"].queryset = tikina_queryset
        self.fields["village"].queryset = koro_queryset
        self.fields["village"].widget.koro_tikina_ids = {
            str(koro.pk): str(koro.tikina_id) for koro in koro_queryset
        }
        self._selected_tikina = None
        self._selected_koro = None
        if not instance:
            self.fields["password1"].required = True
            self.fields["password2"].required = True
            return

        profile, _ = TuragaProfile.objects.get_or_create(user=instance)
        role = getattr(getattr(instance, "user_profile", None), "role", "") or {
            TuragaProfile.TURAGA_NI_KORO: UserProfile.TURAGA_NI_KORO,
            TuragaProfile.MATA_NI_TIKINA: UserProfile.MATA_NI_TIKINA,
            TuragaProfile.TURAGA_NI_YAVUSA: UserProfile.LIULIU_NI_YAVUSA,
            TuragaProfile.ROKO: UserProfile.ROKO_ADMIN,
        }.get(profile.membership_type, UserProfile.TURAGA_NI_KORO)
        self.initial.update(
            {
                "role": role,
                "username": instance.username,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "email": instance.email,
                "is_active": instance.is_active,
                "date_of_birth": profile.date_of_birth,
                "appointment_date": profile.appointment_date,
                "province": profile.province or "Lau",
                "phone_number": profile.phone_number,
                "tokatoka": profile.tokatoka,
                "mataqali": profile.mataqali,
                "yavusa": profile.yavusa,
                "vanua": profile.vanua,
            }
        )
        selected_tikina = self._find_tikina(tikina_queryset, profile.district)
        if selected_tikina:
            self.fields["district"].initial = selected_tikina.pk
            selected_koro = self._find_koro(koro_queryset, profile.village, selected_tikina)
            if selected_koro:
                self.fields["village"].initial = selected_koro.pk

    @staticmethod
    def _normalise_place_name(value):
        return " ".join(str(value or "").strip().upper().split())

    def _find_tikina(self, queryset, value):
        normalised = self._normalise_place_name(value)
        if not normalised:
            return None
        return next((tikina for tikina in queryset if self._normalise_place_name(tikina.name) == normalised), None)

    def _find_koro(self, queryset, value, tikina):
        normalised = self._normalise_place_name(value)
        if not normalised:
            return None
        return next(
            (
                koro
                for koro in queryset
                if koro.tikina_id == tikina.pk and self._normalise_place_name(koro.name) == normalised
            ),
            None,
        )

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = get_user_model().objects.filter(username__iexact=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_district(self):
        self._selected_tikina = self.cleaned_data.get("district")
        return self._selected_tikina.name if self._selected_tikina else ""

    def clean_village(self):
        self._selected_koro = self.cleaned_data.get("village")
        return self._selected_koro.name if self._selected_koro else ""

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        required = {
            UserProfile.TURAGA_NI_KORO: ("date_of_birth", "appointment_date", "village", "district"),
            UserProfile.MATA_NI_TIKINA: ("date_of_birth", "village", "district"),
            UserProfile.LIULIU_NI_YAVUSA: ("tokatoka", "mataqali", "yavusa", "vanua"),
        }.get(role, ())
        for field in required:
            if not cleaned.get(field):
                self.add_error(field, "This field is required for the selected role.")
        if (
            self._selected_tikina
            and self._selected_koro
            and self._selected_koro.tikina_id != self._selected_tikina.pk
        ):
            self.add_error("village", "Select a Koro that belongs to the chosen Tikina.")

        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "The two password fields did not match.")
            else:
                user = self.instance or get_user_model()(username=cleaned.get("username"))
                try:
                    password_validation.validate_password(password1, user)
                except ValidationError as error:
                    self.add_error("password1", error)
        return cleaned

    @transaction.atomic
    def save(self):
        user = self.instance or get_user_model()()
        user.username = self.cleaned_data["username"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.is_active = self.cleaned_data["is_active"]
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        user.save()

        profile, _ = TuragaProfile.objects.get_or_create(user=user)
        role = self.cleaned_data["role"]
        profile.membership_type = ROLE_TO_MEMBERSHIP[role]
        for field in (
            "date_of_birth",
            "appointment_date",
            "village",
            "district",
            "province",
            "phone_number",
            "tokatoka",
            "mataqali",
            "yavusa",
            "vanua",
        ):
            empty_value = None if field in {"date_of_birth", "appointment_date"} else ""
            setattr(profile, field, self.cleaned_data.get(field) or empty_value)
        profile.save()

        sync_user_role(user, role)
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_profile.role = role
        user_profile.tikina = profile.district
        user_profile.koro = profile.village
        user_profile.yavusa = profile.yavusa
        user_profile.phone = profile.phone_number
        user_profile.save()

        if role == UserProfile.ROKO_ADMIN:
            group, _ = Group.objects.get_or_create(name=UserProfile.ROKO_ADMIN)
            user.groups.add(group)
        return user


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(label="New password", strip=False, widget=forms.PasswordInput(attrs={"class": INPUT}))
    password2 = forms.CharField(label="Confirm password", strip=False, widget=forms.PasswordInput(attrs={"class": INPUT}))

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2:
            if password1 != password2:
                self.add_error("password2", "The two password fields did not match.")
            else:
                try:
                    password_validation.validate_password(password1, self.user)
                except ValidationError as error:
                    self.add_error("password1", error)
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["password1"])
        self.user.save(update_fields=["password"])
        return self.user
