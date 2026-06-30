from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="list"),
    path("manage/", views.DocumentManageView.as_view(), name="manage"),
    path("manage/upload/", views.DocumentUploadView.as_view(), name="upload"),
    path("manage/<slug:slug>/edit/", views.DocumentUpdateView.as_view(), name="edit"),
    path("manage/<slug:slug>/delete/", views.DocumentDeleteView.as_view(), name="delete"),
    path("category/<slug:slug>/", views.DocumentCategoryView.as_view(), name="category"),
    path("<slug:slug>/download/", views.DocumentDownloadView.as_view(), name="download"),
    path("<slug:slug>/", views.DocumentDetailView.as_view(), name="detail"),
]
