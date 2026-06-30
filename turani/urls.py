from django.urls import path
from . import views

app_name = "turani"

urlpatterns = [
    path("", views.report_list, name="report_list"),
    path("dashboard/turaga-ni-koro/", views.turaga_dashboard, name="turaga_dashboard"),
    path("create/", views.report_create, name="report_create"),
    path("<int:pk>/edit/", views.report_edit, name="report_edit"),
    path("<int:pk>/", views.report_detail, name="report_detail"),
]
