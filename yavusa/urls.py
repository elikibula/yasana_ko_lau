from django.urls import path

from .views import YavusaDashboardView

app_name = "yavusa"

urlpatterns = [
    path("", YavusaDashboardView.as_view(), name="dashboard"),
]
