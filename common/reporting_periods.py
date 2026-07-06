from calendar import monthrange
from datetime import date

from django.utils import timezone


QUARTER_CHOICES = (
    ("Q1", "Q1 - Feperueri kina Epereli"),
    ("Q2", "Q2 - Me kina Jiulai"),
    ("Q3", "Q3 - Okosita kina Okotopa"),
    ("Q4", "Q4 - Noveba kina Janueri"),
)

QUARTER_DUE_MONTHS = {
    "Q1": 4,
    "Q2": 7,
    "Q3": 10,
    "Q4": 1,
}


def reporting_due_date(quarter, year):
    if not quarter or not year:
        return None

    due_month = QUARTER_DUE_MONTHS.get(quarter)
    if not due_month:
        return None

    due_year = int(year) + 1 if quarter == "Q4" else int(year)
    return date(due_year, due_month, monthrange(due_year, due_month)[1])


def is_report_overdue(report, today=None):
    due_date = reporting_due_date(report.quarter, report.year)
    if not due_date:
        return False

    today = today or timezone.localdate()
    return report.status != report.STATUS_SUBMITTED and due_date < today


def count_overdue_reports(*querysets, today=None):
    return sum(
        1
        for queryset in querysets
        for report in queryset
        if is_report_overdue(report, today=today)
    )
