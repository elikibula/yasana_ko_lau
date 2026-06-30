from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.NewsListView.as_view(), name="list"),
    path("manage/", views.NewsManageView.as_view(), name="manage"),
    path("manage/create/", views.NewsCreateView.as_view(), name="create"),
    path("manage/<slug:slug>/edit/", views.NewsUpdateView.as_view(), name="edit"),
    path("manage/<slug:slug>/delete/", views.NewsDeleteView.as_view(), name="delete"),
    path("category/<slug:slug>/", views.NewsCategoryView.as_view(), name="category"),
    path("<slug:slug>/", views.NewsDetailView.as_view(), name="detail"),
]
