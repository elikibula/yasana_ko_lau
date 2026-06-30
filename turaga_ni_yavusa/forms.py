from django import forms
from django.forms import inlineformset_factory

from common.form_mixins import StyledInlineFormSet, StyledModelFormMixin

from .models import Signature, TNYReport


TNY_FIJIAN_INLINE_LABELS = {
    "Signature": {
        "role": "iTutu",
        "name": "Yaca",
        "signed": "Sa Saini",
        "signed_date": "Tiki ni Siga",
    }
}


class TNYInlineFormSet(StyledInlineFormSet):
    inline_labels = TNY_FIJIAN_INLINE_LABELS


class TNYReportForm(StyledModelFormMixin, forms.ModelForm):
    class Meta:
        model = TNYReport
        exclude = ["owner", "status", "submitted_at", "created_at", "updated_at"]
        labels = {
            "quarter": "Ripote ni vula ko",
            "year": "Ena yabaki ko",
            "full_name": "Yacamuni",
            "tokatoka": "Tokatoka",
            "mataqali": "Mataqali",
            "yavusa": "Yavusa",
            "vanua": "Vanua",
            "koro": "Koro",
            "bosevanua_meeting_frequency": "E vica na Bosevanua ena vula 3 sa oti?",
            "bosevanua_turaga_ni_mataqali_count": "Wiliwili ni Turaga ni Mataqali",
            "bosevanua_liuliu_ni_tokatoka_count": "Wiliwili ni Liuliu ni Tokatoka",
            "bosevanua_lewe_ni_yavusa_count": "Wiliwili ni Lewe ni Yavusa",
            "genealogy_recorded_count": "Wiliwili era Volai ena iVola ni Kawa Bula",
            "genealogy_removed_count": "Wiliwili era Bokoci ena iVola ni Kawa Bula",
            "yavusa_report_filed": "Sa vakacurumi na ripote ni Yavusa?",
            "yavusa_report_topics": "Veika bibi e volai ena ripote",
            "yavusa_report_notes": "iKuri ni vakamacala ni ripote",
            "confirmed_titles_this_period": "Wiliwili ni itutu vakavanua sa vakadeitaki",
            "titles_additional_notes": "iKuri ni vakamacala ni itutu",
            "language_custom_initiatives": "Tuvatuva ni vosa, itovo kei na kilaka vakavanua",
            "land_initiatives": "Tuvatuva ni qele",
            "fishing_ground_initiatives": "Tuvatuva ni qoliqoli",
            "resident_turaga_count": "Turaga era tiko ena koro",
            "resident_marama_count": "Marama era tiko ena koro",
            "resident_gone_count": "Gone era tiko ena koro",
            "away_turaga_count": "Turaga era tiko tani",
            "away_marama_count": "Marama era tiko tani",
            "away_gone_count": "Gone era tiko tani",
            "has_member_visitation_plan": "E tiko na tuvatuva ni sikovi ira na lewe ni Yavusa?",
            "attends_bose_vakoro": "Dau tiko ena Bose Vakoro?",
            "attends_bose_ni_tikina": "Dau tiko ena Bose ni Tikina?",
            "churches_in_yavusa_count": "Wiliwili ni veimatalotu ena Yavusa",
            "church_follows_vanua_program": "E muria na lotu na tuvatuva ni Vanua?",
            "church_meets_vanua_needs": "E sotava na lotu na gagadre ni Vanua?",
            "yavusa_obligations": "Bolebole kei na kauwai ni Yavusa",
            "mataqali_obligations": "Bolebole kei na kauwai ni Mataqali",
            "tokatoka_obligations": "Bolebole kei na kauwai ni Tokatoka",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = field.help_text or "Complete this field for the quarterly Turaga ni Yavusa report."


SignatureFormSet = inlineformset_factory(
    TNYReport,
    Signature,
    fields=["role", "name", "signed", "signed_date"],
    extra=len(Signature.ROLE_CHOICES),
    can_delete=False,
    formset=TNYInlineFormSet,
)


TNY_SECTIONS = (
    ("NA KEMU ITUKUTUKU", ("quarter", "year", "full_name", "tokatoka", "mataqali", "yavusa", "vanua", "koro")),
    ("NA BOSEVANUA", ("bosevanua_meeting_frequency", "bosevanua_turaga_ni_mataqali_count", "bosevanua_liuliu_ni_tokatoka_count", "bosevanua_lewe_ni_yavusa_count", "genealogy_recorded_count", "genealogy_removed_count", "yavusa_report_filed", "yavusa_report_topics", "yavusa_report_notes")),
    ("NA VAKATAWANI NI ITUTU VAKAVANUA", ("confirmed_titles_this_period", "titles_additional_notes")),
    ("NA IYAU BULA", ("language_custom_initiatives", "land_initiatives", "fishing_ground_initiatives")),
    ("NA NODRA SIKOVI NA LEWE NI YAVUSA", ("resident_turaga_count", "resident_marama_count", "resident_gone_count", "away_turaga_count", "away_marama_count", "away_gone_count", "has_member_visitation_plan")),
    ("NA BOSE VAKORO KEI NA BOSE NI TIKINA", ("attends_bose_vakoro", "attends_bose_ni_tikina")),
    ("NA VEISEMATI NI VANUA KEI NA VEIMATALOTU", ("churches_in_yavusa_count", "church_follows_vanua_program", "church_meets_vanua_needs")),
    ("BOLEBOLE KEI NA KAUWAI", ("yavusa_obligations", "mataqali_obligations", "tokatoka_obligations")),
)


TNY_FORMSET_TITLES = {"signatures": "VAKADINADINA"}
