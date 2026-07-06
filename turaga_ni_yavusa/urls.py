from django.urls import path

from . import views


app_name = "turaga_ni_yavusa"

urlpatterns = [
    path("", views.report_list, name="report_list"),
    path("dashboard/", views.turaga_ni_yavusa_dashboard, name="turaga_ni_yavusa_dashboard"),
    path("create/", views.report_create, name="report_create"),
    path("<int:pk>/edit/", views.report_edit, name="report_edit"),
    path("<int:pk>/workflow/<str:action_type>/", views.report_workflow_action, name="report_workflow_action"),
    path("<int:pk>/pdf/", views.report_pdf, name="report_pdf"),
    path("<int:pk>/", views.report_detail, name="report_detail"),
]
