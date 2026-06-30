from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("tikina/", views.TikinaListView.as_view(), name="tikina"),
    path("news/", views.NewsListView.as_view(), name="news_list"),
    path("news/<slug:slug>/", views.NewsDetailView.as_view(), name="news_detail"),
    path("contact/", views.contact, name="contact"),
]
