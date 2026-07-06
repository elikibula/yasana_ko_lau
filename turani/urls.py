from django.urls import path
from . import views

app_name = "turani"

urlpatterns = [
    path("", views.report_list, name="report_list"),
    path("dashboard/turaga-ni-koro/", views.turaga_dashboard, name="turaga_dashboard"),
    path("create/", views.report_create, name="report_create"),
    path("<int:pk>/edit/", views.report_edit, name="report_edit"),
    path("<int:pk>/pdf/", views.report_pdf, name="report_pdf"),
    path("<int:pk>/timeline/", views.approval_timeline, name="approval_timeline"),
    path("<int:pk>/submit/", views.report_workflow_action, {"action_type": "submit"}, name="report_submit"),
    path("<int:pk>/approve/", views.report_workflow_action, {"action_type": "approve"}, name="report_approve"),
    path("<int:pk>/return/", views.report_workflow_action, {"action_type": "return"}, name="report_return"),
    path("<int:pk>/reject/", views.report_workflow_action, {"action_type": "reject"}, name="report_reject"),
    path("<int:pk>/recommend/", views.report_workflow_action, {"action_type": "recommend"}, name="report_recommend"),
    path("<int:pk>/final-approve/", views.report_workflow_action, {"action_type": "final_approve"}, name="report_final_approve"),
    path("<int:pk>/archive/", views.report_workflow_action, {"action_type": "archive"}, name="report_archive"),
    path("<int:pk>/comment/", views.report_workflow_action, {"action_type": "comment"}, name="report_comment"),
    path("<int:pk>/", views.report_detail, name="report_detail"),
]
