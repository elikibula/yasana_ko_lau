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
            "phone_number": "Naba ni Talevoni",
            "email": "Email",
            "tokatoka": "Tokatoka",
            "mataqali": "Mataqali",
            "yavusa": "Yavusa",
            "vanua": "Vanua",
            "koro": "Koro",
            "tikina": "Tikina",
            "bosevanua_meeting_frequency": "Sa dau dabe rawa vakavica na nomuni matabose ni Vanua?",
            "bosevanua_turaga_ni_mataqali_count": "Wiliwili ni Turaga ni Mataqali era tiko kina",
            "bosevanua_liuliu_ni_tokatoka_count": "Wiliwili ni Liuliu ni Tokatoka era tiko kina",
            "bosevanua_lewe_ni_yavusa_count": "Wiliwili ni Lewe ni Yavusa era tiko kina",
            "genealogy_recorded_count": "Wiliwili era Volai ena iVola ni Kawa Bula",
            "genealogy_removed_count": "Wiliwili era Bokoci ena iVola ni Kawa Bula",
            "yavusa_report_filed": "E tiko na Tukutuku Raraba ni Yavusa",
            "yavusa_report_topics": "Veika tale eso me baleta na Matabose ni Vanua ka vakayacori",
            "yavusa_report_notes": "iKuri ni vakamacala me baleta na veika e mai Bosei ena Matabose ni Vanua sa vakayacori rawa",
            "confirmed_titles_this_period": "E vica nai tutu ni Turaga ni Mataqali sa vakadeitaki ena nomu Yavusa",
            "titles_additional_notes": "iKuri ni vakamacala me baleta na kedra vakatawani na vei iTutu Vakavanua ena loma ni Yavusa",
            "language_custom_initiatives": "Tuvatuva ni Tamata, itovo kei na kilaka vakavanua",
            "land_initiatives": "Tuvatuva ni iYau bula me baleta na qele",
            "fishing_ground_initiatives": "Tuvatuva ni iYau bula me baleta na qoliqoli",
            "resident_turaga_count": "E vica na lewe ni nomu Yavusa Turaga era tiko e Vanua?",
            "resident_marama_count": "E vica na lewe ni nomu Yavusa Marama era tiko e Vanua?",
            "resident_gone_count": "E vica na lewe ni nomu Yavusa Gone era tiko e Vanua?",
            "away_turaga_count": "E vica na lewe ni nomu Yavusa Turaga era tiko e Vanua ni Cakacaka?",
            "away_marama_count": "E vica na lewe ni nomu Yavusa Marama era tiko e Vanua ni Cakacaka?",
            "away_gone_count": "E vica na lewe ni nomu Yavusa Gone era tiko e Vanua ni Cakacaka?",
            "has_member_visitation_plan": "E tiko beka edua na nomuni tuvatuva mera sikovi ira na lewe ni Yavusa tu ena vale ni veivakadodonutaki?",
            "attends_bose_vakoro": "Koni dau tiko ena Bose Vakoro?",
            "attends_bose_ni_tikina": "Koni dau tiko ena Bose ni Tikina?",
            "churches_in_yavusa_count": "E vica na matalotu era tiko ena loma ni nomuni Yavusa?",
            "church_follows_vanua_program": "E dau cabe taka nona ituvatuva na Lotu kina Vanua?",
            "church_meets_vanua_needs": "E sotava tiko na lotu na gagadre ni Vanua?",
            "yavusa_obligations": "Bolebole kei na kauwai ena loma ni ni Yavusa",
            "mataqali_obligations": "Bolebole kei na kauwai ni ena loma ni Mataqali",
            "tokatoka_obligations": "Bolebole kei na kauwai ni ena loma ni Tokatoka",
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
    ("NA KEMU ITUKUTUKU", ("quarter", "year", "full_name", "phone_number", "email", "tokatoka", "mataqali", "yavusa", "vanua", "koro", "tikina")),
    ("NA MATABOSE NI VANUA", ("bosevanua_meeting_frequency", "bosevanua_turaga_ni_mataqali_count", "bosevanua_liuliu_ni_tokatoka_count", "bosevanua_lewe_ni_yavusa_count", "genealogy_recorded_count", "genealogy_removed_count", "yavusa_report_filed", "yavusa_report_topics", "yavusa_report_notes")),
    ("NA VAKATAWANI NI ITUTU VAKAVANUA", ("confirmed_titles_this_period", "titles_additional_notes")),
    ("NA CAVA SOTI ESA BAU QARAVI RAWA ENA VUKU NI IYAU BULA", ("language_custom_initiatives", "land_initiatives", "fishing_ground_initiatives")),
    ("NA NODRA SIKOVI NA LEWE NI YAVUSA", ("resident_turaga_count", "resident_marama_count", "resident_gone_count", "away_turaga_count", "away_marama_count", "away_gone_count", "has_member_visitation_plan")),
    ("NA BOSE VAKORO KEI NA BOSE NI TIKINA", ("attends_bose_vakoro", "attends_bose_ni_tikina")),
    ("NA VEISEMATI NI VANUA KEI NA VEIMATALOTU", ("churches_in_yavusa_count", "church_follows_vanua_program", "church_meets_vanua_needs")),
    ("BOLEBOLE KEI NA KAUWAI", ("yavusa_obligations", "mataqali_obligations", "tokatoka_obligations")),
)
