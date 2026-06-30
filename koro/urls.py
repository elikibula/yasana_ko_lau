from django.urls import path

from .views import KoroDetailView, KoroListView

app_name = "koro"

urlpatterns = [
    path("", KoroListView.as_view(), name="list"),
    path("<slug:slug>/", KoroDetailView.as_view(), name="detail"),
]
