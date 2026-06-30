from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.shortcuts import render

from documents.models import Document
from events.models import Event
from koro.models import KoroReport
from news.models import NewsPost
from tikina.models import Tikina, TikinaReport
from yavusa.models import YavusaReport


def is_roko_admin(user):
    return user.groups.filter(name="roko_admin").exists()


@login_required
@user_passes_test(is_roko_admin)
def dashboard(request):
    koro_reports = KoroReport.objects.select_related("tikina")
    tikina_reports = TikinaReport.objects.select_related("tikina")
    yavusa_reports = YavusaReport.objects.all()
    tikina_summary = []
    for tikina in Tikina.objects.prefetch_related("koro").annotate(
        reports_submitted=Count("koro_reports"),
        pending_reports=Count("koro_reports", filter=Q(koro_reports__status="pending")),
    ):
        tikina_summary.append(
            {
                "tikina": tikina,
                "reports_submitted": tikina.reports_submitted,
                "pending": tikina.pending_reports,
            }
        )
    context = {
        "total_submissions": koro_reports.count() + tikina_reports.count() + yavusa_reports.count(),
        "pending_count": (
            koro_reports.filter(status="pending").count()
            + tikina_reports.filter(status="pending").count()
            + yavusa_reports.filter(status="pending").count()
        ),
        "approved_count": (
            koro_reports.filter(status="approved").count()
            + tikina_reports.filter(status="approved").count()
            + yavusa_reports.filter(status="approved").count()
        ),
        "overdue_count": 0,
        "koro_reports": koro_reports[:12],
        "tikina_reports": tikina_reports[:8],
        "yavusa_reports": yavusa_reports[:8],
        "news_published_count": NewsPost.objects.filter(status="published").count(),
        "news_draft_count": NewsPost.objects.filter(status="draft").count(),
        "upcoming_events_count": Event.objects.filter(status="upcoming").count(),
        "documents_total_count": Document.objects.count(),
        "documents_public_count": Document.objects.filter(access_level="public").count(),
        "documents_restricted_count": Document.objects.exclude(access_level="public").count(),
        "tikina_summary": tikina_summary,
    }
    return render(request, "dashboard/admin/index.html", context)
