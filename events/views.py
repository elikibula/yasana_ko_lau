import json
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from accounts.mixins import RoleRequiredMixin
from koro.models import TIKINA_CHOICES

from .forms import EventForm
from .models import Event, EventCategory, EventRSVP


class EventListView(ListView):
    model = Event
    template_name = "events/list.html"
    context_object_name = "events"
    paginate_by = 9

    def get_queryset(self):
        qs = Event.objects.select_related("category").prefetch_related("rsvps")
        status = self.request.GET.get("status", "upcoming")
        category = self.request.GET.get("category")
        tikina = self.request.GET.get("tikina")
        if status and status != "all":
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category__slug=category)
        if tikina:
            qs = qs.filter(tikina=tikina)
        return qs.order_by("start_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context.update(
            {
                "categories": EventCategory.objects.all(),
                "tikina_choices": TIKINA_CHOICES,
                "selected_status": self.request.GET.get("status", "upcoming"),
                "selected_category": self.request.GET.get("category", ""),
                "selected_tikina": self.request.GET.get("tikina", ""),
                "upcoming_count": Event.objects.filter(start_date__gte=now, status="upcoming").count(),
                "featured_event": Event.objects.filter(is_featured=True, start_date__gte=now).order_by("start_date").first(),
            }
        )
        return context


class EventCalendarView(TemplateView):
    template_name = "events/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        events = Event.objects.filter(start_date__year=today.year, start_date__month=today.month).order_by("start_date")
        grouped = defaultdict(list)
        for event in events:
            grouped[event.start_date.date().isoformat()].append(
                {"title": event.title, "url": event.get_absolute_url() if hasattr(event, "get_absolute_url") else f"/events/{event.slug}/"}
            )
        context["month_events"] = events
        context["events_json"] = json.dumps(grouped)
        context["current_month"] = today
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.select_related("category", "created_by").prefetch_related("rsvps")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_rsvp = None
        if self.request.user.is_authenticated:
            user_rsvp = self.object.rsvps.filter(user=self.request.user).first()
        context["user_rsvp"] = user_rsvp
        context["attending_count"] = self.object.rsvps.filter(attending=True).count()
        return context


class EventRSVPView(LoginRequiredMixin, View):
    def post(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        attending = request.POST.get("attending") == "true"
        note = request.POST.get("note", "")
        EventRSVP.objects.update_or_create(
            event=event,
            user=request.user,
            defaults={"attending": attending, "note": note},
        )
        messages.success(request, "Your RSVP has been saved.")
        return redirect("events:detail", slug=slug)

    def get(self, request, slug):
        return HttpResponseNotAllowed(["POST"])


class EventManageView(RoleRequiredMixin, ListView):
    required_group = "roko_admin"
    model = Event
    template_name = "events/manage/list.html"
    context_object_name = "events"
    paginate_by = 20

    def get_queryset(self):
        return Event.objects.select_related("category", "created_by").prefetch_related("rsvps").order_by("-start_date")


class EventCreateView(RoleRequiredMixin, CreateView):
    required_group = "roko_admin"
    model = Event
    form_class = EventForm
    template_name = "events/manage/form.html"
    success_url = reverse_lazy("events:manage")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Event saved.")
        return super().form_valid(form)


class EventUpdateView(RoleRequiredMixin, UpdateView):
    required_group = "roko_admin"
    model = Event
    form_class = EventForm
    template_name = "events/manage/form.html"
    success_url = reverse_lazy("events:manage")

    def form_valid(self, form):
        messages.success(self.request, "Event updated.")
        return super().form_valid(form)


class EventDeleteView(RoleRequiredMixin, DeleteView):
    required_group = "roko_admin"
    model = Event
    template_name = "events/manage/confirm_delete.html"
    success_url = reverse_lazy("events:manage")

    def form_valid(self, form):
        messages.success(self.request, "Event deleted.")
        return super().form_valid(form)


class EventRSVPListView(RoleRequiredMixin, DetailView):
    required_group = "roko_admin"
    model = Event
    template_name = "events/manage/rsvp_list.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rsvps"] = self.object.rsvps.select_related("user")
        return context
