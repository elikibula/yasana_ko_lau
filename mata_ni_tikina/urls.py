from django.urls import path

from . import views


app_name = "mata_ni_tikina"

urlpatterns = [
    path("", views.report_list, name="report_list"),
    path("dashboard/", views.mata_ni_tikina_dashboard, name="mata_ni_tikina_dashboard"),
    path("create/", views.report_create, name="report_create"),
    path("<int:pk>/edit/", views.report_edit, name="report_edit"),
    path("<int:pk>/", views.report_detail, name="report_detail"),
]
