from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventListView.as_view(), name="list"),
    path("calendar/", views.EventCalendarView.as_view(), name="calendar"),
    path("manage/", views.EventManageView.as_view(), name="manage"),
    path("manage/create/", views.EventCreateView.as_view(), name="create"),
    path("manage/<slug:slug>/edit/", views.EventUpdateView.as_view(), name="edit"),
    path("manage/<slug:slug>/delete/", views.EventDeleteView.as_view(), name="delete"),
    path("manage/<slug:slug>/rsvps/", views.EventRSVPListView.as_view(), name="rsvp_list"),
    path("<slug:slug>/rsvp/", views.EventRSVPView.as_view(), name="rsvp"),
    path("<slug:slug>/", views.EventDetailView.as_view(), name="detail"),
]
