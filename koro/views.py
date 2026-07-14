from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView
from django.db.models import Count

from accounts.mixins import RoleRequiredMixin
from events.models import Event
from news.models import NewsPost
from tikina.models import Tikina
from turani.models import TNKReport

from .models import Koro, KoroReport


class KoroListView(ListView):
    model = Koro
    template_name = "koro/list.html"
    context_object_name = "koro_list"

    def get_queryset(self):
        qs = Koro.objects.select_related("tikina", "turaga_ni_koro", "turaga_ni_koro__user")
        tikina = self.request.GET.get("tikina")
        if tikina:
            qs = qs.filter(tikina__slug=tikina)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tikina_list"] = Tikina.objects.all()
        context["selected_tikina"] = self.request.GET.get("tikina", "")
        return context


class KoroDetailView(DetailView):
    model = Koro
    template_name = "koro/detail.html"
    context_object_name = "koro"

    def get_queryset(self):
        return Koro.objects.select_related("tikina", "turaga_ni_koro", "turaga_ni_koro__user").prefetch_related("drone_videos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tikina"] = self.object.tikina
        context["recent_reports"] = KoroReport.objects.filter(koro_name__iexact=self.object.name).select_related("tikina")[:5]
        return context


class KoroDashboardView(RoleRequiredMixin, TemplateView):
    required_group = "turaga_ni_koro"
    template_name = "dashboard/koro/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reports = KoroReport.objects.filter(submitted_by=self.request.user).select_related("tikina")
        profile = getattr(self.request.user, "user_profile", None)
        assigned_koro = Koro.objects.filter(turaga_ni_koro=profile).select_related("tikina").first() if profile else None
        if not assigned_koro and profile and profile.koro:
            assigned_koro = Koro.objects.filter(name__iexact=profile.koro).select_related("tikina").first()
        tnk_reports = TNKReport.objects.filter(owner=self.request.user).order_by("-year", "-created_at")
        context.update(
            {
                "profile": profile,
                "assigned_koro": assigned_koro,
                "assigned_tikina": assigned_koro.tikina if assigned_koro else None,
                "reports": reports[:8],
                "last_submission": reports.first(),
                "tnk_latest": tnk_reports[:5],
                "tnk_total": tnk_reports.count(),
                "tnk_quarters": tnk_reports.values("quarter", "year").distinct().order_by("-year", "quarter")[:8],
                "today": timezone.localdate(),
                "latest_news": NewsPost.objects.filter(status="published", published_at__isnull=False)[:3],
                "upcoming_events": Event.objects.filter(status="upcoming", start_date__gte=timezone.now())[:2],
            }
        )
        return context
