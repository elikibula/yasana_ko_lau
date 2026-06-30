from django.contrib import admin

from .models import Document, DocumentCategory


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "icon"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "file_type", "access_level", "year", "download_count", "uploaded_by", "created_at"]
    list_filter = ["access_level", "file_type", "category", "year"]
    search_fields = ["title", "description", "tags"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["download_count", "file_size_kb", "created_at", "updated_at"]
