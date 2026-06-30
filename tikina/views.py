from django.views.generic import DetailView, ListView, TemplateView
from django.utils import timezone
from django.db.models import Count, Sum

from accounts.mixins import RoleRequiredMixin
from events.models import Event
from koro.models import KoroReport, TIKINA_CHOICES
from news.models import NewsPost
from mata_ni_tikina.models import MNTReport

from .models import Tikina, TikinaReport


class TikinaListView(ListView):
    model = Tikina
    template_name = "tikina/list.html"
    context_object_name = "tikina_list"

    def get_queryset(self):
        qs = (
            Tikina.objects.filter(is_active=True)
            .prefetch_related("koro", "gallery_images")
            .select_related("mata_ni_tikina__user")
            .annotate(koro_db_count=Count("koro"))
            .order_by("number")
        )
        island_group = self.request.GET.get("island_group")
        if island_group:
            qs = qs.filter(island_group__iexact=island_group)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context["tikina_list"]
        context["total_koro_count"] = sum(tikina.koro_db_count for tikina in qs)
        context["total_population"] = sum(tikina.population or 0 for tikina in qs)
        context["island_groups"] = (
            Tikina.objects.filter(is_active=True)
            .exclude(island_group="")
            .values_list("island_group", flat=True)
            .distinct()
            .order_by("island_group")
        )
        context["active_island_group"] = self.request.GET.get("island_group", "")
        return context


class TikinaDetailView(DetailView):
    model = Tikina
    template_name = "tikina/detail.html"
    context_object_name = "tikina"

    def get_queryset(self):
        return (
            Tikina.objects.prefetch_related(
                "koro",
                "koro__turaga_ni_koro__user",
                "gallery_images",
                "reports",
            )
            .select_related("mata_ni_tikina__user")
            .order_by("number")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tikina = self.object
        context["koro_list"] = tikina.koro.select_related("turaga_ni_koro__user").order_by("-is_koro_turaga", "name")
        context["reports_summary"] = {
            "submitted": tikina.reports.count(),
            "pending": tikina.reports.filter(status="pending").count(),
            "approved": tikina.reports.filter(status="approved").count(),
        }
        context["gallery_images"] = tikina.gallery_images.all()
        context["latest_news"] = NewsPost.objects.filter(
            status="published", published_at__isnull=False
        ).order_by("-published_at")[:4]
        context["upcoming_events"] = Event.objects.filter(
            status="upcoming", start_date__gte=timezone.now()
        ).order_by("start_date")[:3]
        return context


class TikinaDashboardView(RoleRequiredMixin, TemplateView):
    required_group = "mata_ni_tikina"
    template_name = "dashboard/tikina/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.request.user, "user_profile", None)
        assigned_tikina = Tikina.objects.filter(mata_ni_tikina=profile).first() if profile else None
        if not assigned_tikina and profile and profile.tikina:
            assigned_tikina = Tikina.objects.filter(name__iexact=profile.tikina).first()
        tikina_name = assigned_tikina.name if assigned_tikina else (profile.tikina if profile and profile.tikina else "")
        koro_reports = (
            KoroReport.objects.filter(tikina_id=assigned_tikina.pk).select_related("tikina")
            if assigned_tikina
            else KoroReport.objects.none()
        )
        mata_reports = MNTReport.objects.filter(
            owner=self.request.user
        ).order_by("-year", "-created_at")
        context.update(
            {
                "profile": profile,
                "assigned_tikina": assigned_tikina,
                "assigned_koro_list": assigned_tikina.koro.select_related("turaga_ni_koro__user") if assigned_tikina else [],
                "koro_turaga_village": assigned_tikina.koro_turaga_village if assigned_tikina else None,
                "tikina_name": tikina_name or "Assigned Tikina",
                "tikina_reports": TikinaReport.objects.filter(
                    submitted_by=self.request.user
                ).select_related("tikina")[:6],
                "mata_latest": mata_reports[:5],
                "mata_total": mata_reports.count(),
                "mata_levy_paid": mata_reports.aggregate(s=Sum("soli_collected_amount"))["s"] or 0,
                "mata_levy_target": mata_reports.aggregate(s=Sum("soli_target_amount"))["s"] or 0,
                "mata_total_pop": mata_reports.aggregate(s=Sum("tikina_population"))["s"] or 0,
                "koro_reports": koro_reports[:10],
                "tikina_choices": TIKINA_CHOICES,
                "latest_news": NewsPost.objects.filter(
                    status="published", published_at__isnull=False
                ).order_by("-published_at")[:3],
                "upcoming_events": Event.objects.filter(
                    status="upcoming", start_date__gte=timezone.now()
                ).order_by("start_date")[:2],
            }
        )
        return context
