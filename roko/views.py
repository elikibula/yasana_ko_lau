from itertools import chain

from django.db.models import Count, Sum
from django.shortcuts import render

from accounts.decorators import membership_required
from accounts.models import TuragaProfile
from mata_ni_tikina.models import MNTReport
from turaga_ni_yavusa.models import TNYReport
from turani.analytics import tnk_dashboard_analysis
from turani.models import Business, IVDPProject, LawOffence, PopulationAgeGroup, TNKReport


@membership_required(TuragaProfile.ROKO, allow_roko=True)
def dashboard(request):
    tnk_reports = TNKReport.objects.all()
    mata_reports = MNTReport.objects.all()
    yavusa_reports = TNYReport.objects.all()
    tnk_analysis = tnk_dashboard_analysis(tnk_reports)
    role_counts = TuragaProfile.objects.values("membership_type").annotate(total=Count("id"))
    resident_totals = yavusa_reports.aggregate(men=Sum("resident_turaga_count"), women=Sum("resident_marama_count"), children=Sum("resident_gone_count"))

    recent = sorted(
        chain(
            ((r.created_at, "Turaga ni Koro", r.village, r.quarter, r.year, "turani:report_detail", r.pk) for r in tnk_reports[:8]),
            ((r.created_at, "Mata ni Tikina", r.tikina, r.quarter, r.year, "mata_ni_tikina:report_detail", r.pk) for r in mata_reports[:8]),
            ((r.created_at, "Turaga ni Yavusa", r.yavusa, r.quarter, r.year, "turaga_ni_yavusa:report_detail", r.pk) for r in yavusa_reports[:8]),
        ),
        key=lambda item: item[0],
        reverse=True,
    )[:12]

    context = {
        "total_reports": tnk_reports.count() + mata_reports.count() + yavusa_reports.count(),
        "tnk_report_count": tnk_reports.count(),
        "mata_report_count": mata_reports.count(),
        "yavusa_report_count": yavusa_reports.count(),
        "reporter_count": TuragaProfile.objects.exclude(membership_type=TuragaProfile.ROKO).count(),
        "tnk_population": PopulationAgeGroup.objects.aggregate(total=Sum("count"))["total"] or 0,
        "district_population": mata_reports.aggregate(total=Sum("tikina_population"))["total"] or 0,
        "yavusa_residents": sum(resident_totals.get(key) or 0 for key in ("men", "women", "children")),
        "offence_count": LawOffence.objects.aggregate(total=Sum("count"))["total"] or 0,
        "business_count": Business.objects.count(),
        "project_count": IVDPProject.objects.count() + mata_reports.exclude(govt_projects_covered="").count(),
        "government_aid": mata_reports.aggregate(total=Sum("govt_financial_assistance_amount"))["total"] or 0,
        "ngo_aid": mata_reports.aggregate(total=Sum("ngo_financial_assistance_amount"))["total"] or 0,
        "levy_paid": mata_reports.aggregate(total=Sum("soli_collected_amount"))["total"] or 0,
        "tnk_analysis": tnk_analysis,
        "tnk_user_analysis": tnk_reports.values(
            "owner__first_name", "owner__last_name", "owner__username"
        )
        .annotate(
            reports=Count("id"),
            households=Sum("household_count"),
            meetings=Sum("village_meetings_count"),
        )
        .order_by("owner__first_name", "owner__last_name"),
        "role_counts": role_counts,
        "recent_reports": recent,
    }
    return render(request, "roko/dashboard.html", context)
