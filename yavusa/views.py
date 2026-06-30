from django.views.generic import TemplateView
from django.utils import timezone

from accounts.mixins import RoleRequiredMixin
from events.models import Event
from news.models import NewsPost
from turaga_ni_yavusa.models import TNYReport


class YavusaDashboardView(RoleRequiredMixin, TemplateView):
    required_group = "liuliu_ni_yavusa"
    template_name = "dashboard/yavusa/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.request.user, "user_profile", None)
        reports = TNYReport.objects.filter(owner=self.request.user).order_by("-year", "-created_at")
        latest = reports.first()
        context.update(
            {
                "profile": profile,
                "yavusa_reports": reports[:6],
                "yavusa_total": reports.count(),
                "latest_report": latest,
                "latest_residents": latest.residents_total if latest else 0,
                "latest_away": latest.away_total if latest else 0,
                "latest_births": latest.genealogy_recorded_count if latest else 0,
                "latest_bosevanua": latest.bosevanua_meeting_frequency if latest else 0,
                "latest_news": NewsPost.objects.filter(status="published", published_at__isnull=False)[:3],
                "upcoming_events": Event.objects.filter(status="upcoming", start_date__gte=timezone.now())[:2],
            }
        )
        return context
