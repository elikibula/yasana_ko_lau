from django.conf import settings
from django.db import models
from django.utils import timezone

from common.reporting_periods import (
    QUARTER_CHOICES,
    is_report_overdue,
    reporting_due_date,
)


class TNYReport(models.Model):
    YES_NO = (("io", "Io"), ("sega", "Sega"))
    QUARTERS = QUARTER_CHOICES
    MEETING_FREQUENCY_CHOICES = (("1", "Dua"), ("2", "Rua"), ("3", "Tolu+"))
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED_TO_ROKO = "submitted"
    STATUS_APPROVED_BY_ROKO = "approved_roko"
    STATUS_RETURNED_BY_ROKO = "returned_roko"
    STATUS_REJECTED_BY_ROKO = "rejected_roko"
    STATUS_SUBMITTED = STATUS_SUBMITTED_TO_ROKO
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED_TO_ROKO, "Submitted to Roko Tui"),
        (STATUS_APPROVED_BY_ROKO, "Approved by Roko Tui"),
        (STATUS_RETURNED_BY_ROKO, "Returned by Roko Tui"),
        (STATUS_REJECTED_BY_ROKO, "Rejected by Roko Tui"),
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tny_reports", null=True, blank=True)
    quarter = models.CharField(max_length=2, choices=QUARTERS)
    year = models.PositiveIntegerField()
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    tokatoka = models.CharField(max_length=150)
    mataqali = models.CharField(max_length=150)
    yavusa = models.CharField(max_length=150)
    vanua = models.CharField(max_length=150)
    koro = models.CharField(max_length=150, blank=True)
    tikina = models.CharField(max_length=150, blank=True)
    bosevanua_meeting_frequency = models.CharField(max_length=1, choices=MEETING_FREQUENCY_CHOICES)
    bosevanua_turaga_ni_mataqali_count = models.PositiveIntegerField(default=0)
    bosevanua_liuliu_ni_tokatoka_count = models.PositiveIntegerField(default=0)
    bosevanua_lewe_ni_yavusa_count = models.PositiveIntegerField(default=0)
    genealogy_recorded_count = models.PositiveIntegerField(default=0)
    genealogy_removed_count = models.PositiveIntegerField(default=0)
    yavusa_report_filed = models.CharField(max_length=10, choices=YES_NO, blank=True)
    yavusa_report_topics = models.TextField(blank=True)
    yavusa_report_notes = models.TextField(blank=True)
    confirmed_titles_this_period = models.PositiveIntegerField(default=0)
    titles_additional_notes = models.TextField(blank=True)
    language_custom_initiatives = models.TextField(blank=True)
    land_initiatives = models.TextField(blank=True)
    fishing_ground_initiatives = models.TextField(blank=True)
    resident_turaga_count = models.PositiveIntegerField(default=0)
    resident_marama_count = models.PositiveIntegerField(default=0)
    resident_gone_count = models.PositiveIntegerField(default=0)
    away_turaga_count = models.PositiveIntegerField(default=0)
    away_marama_count = models.PositiveIntegerField(default=0)
    away_gone_count = models.PositiveIntegerField(default=0)
    has_member_visitation_plan = models.CharField(max_length=10, choices=YES_NO, blank=True)
    attends_bose_vakoro = models.CharField(max_length=10, choices=YES_NO, blank=True)
    attends_bose_ni_tikina = models.CharField(max_length=10, choices=YES_NO, blank=True)
    churches_in_yavusa_count = models.PositiveIntegerField(default=0)
    church_follows_vanua_program = models.CharField(max_length=10, choices=YES_NO, blank=True)
    church_meets_vanua_needs = models.CharField(max_length=10, choices=YES_NO, blank=True)
    yavusa_obligations = models.TextField(blank=True)
    mataqali_obligations = models.TextField(blank=True)
    tokatoka_obligations = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-created_at"]
        constraints = [models.UniqueConstraint(fields=["owner", "quarter", "year"], name="one_tny_report_per_owner_quarter")]

    def submit(self):
        self.status = self.STATUS_SUBMITTED_TO_ROKO
        if not self.submitted_at:
            self.submitted_at = timezone.now()

    @property
    def due_date(self):
        return reporting_due_date(self.quarter, self.year)

    @property
    def is_overdue(self):
        return is_report_overdue(self)

    @property
    def residents_total(self):
        return self.resident_turaga_count + self.resident_marama_count + self.resident_gone_count

    @property
    def away_total(self):
        return self.away_turaga_count + self.away_marama_count + self.away_gone_count

    def __str__(self):
        return f"{self.yavusa} - {self.quarter} {self.year}"


class TNYApprovalAction(models.Model):
    ACTION_SUBMIT = "submit"
    ACTION_APPROVE = "approve"
    ACTION_RETURN = "return"
    ACTION_REJECT = "reject"
    ACTION_COMMENT = "comment"
    ACTION_CHOICES = (
        (ACTION_SUBMIT, "Submit"),
        (ACTION_APPROVE, "Approve"),
        (ACTION_RETURN, "Return"),
        (ACTION_REJECT, "Reject"),
        (ACTION_COMMENT, "Comment"),
    )

    report = models.ForeignKey(TNYReport, on_delete=models.PROTECT, related_name="approval_actions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tny_approval_actions")
    user_full_name = models.CharField(max_length=150)
    user_role = models.CharField(max_length=100)
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES)
    from_status = models.CharField(max_length=40, blank=True)
    to_status = models.CharField(max_length=40, blank=True)
    comment = models.TextField(blank=True)
    digital_acknowledgement = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]
        verbose_name = "Turaga ni Yavusa Approval Action"
        verbose_name_plural = "Turaga ni Yavusa Approval Actions"

    def __str__(self):
        return f"{self.report} - {self.get_action_type_display()} by {self.user_full_name}"


class Signature(models.Model):
    ROLE_CHOICES = (
        ("turaga_ni_yavusa", "Turaga ni Yavusa"),
        ("turaga_ni_koro", "Turaga ni Koro"),
        ("roko_veiqaravi", "Roko Veiqaravi"),
        ("roko_tui", "Roko Tui"),
    )
    report = models.ForeignKey(TNYReport, on_delete=models.CASCADE, related_name="signatures")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    name = models.CharField(max_length=150, blank=True)
    signed = models.BooleanField(default=False)
    signed_date = models.DateField(null=True, blank=True)
