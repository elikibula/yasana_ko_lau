from django.urls import path

from .views import TikinaDetailView, TikinaListView

app_name = "tikina"

urlpatterns = [
    path("", TikinaListView.as_view(), name="list"),
    path("<slug:slug>/", TikinaDetailView.as_view(), name="detail"),
]
