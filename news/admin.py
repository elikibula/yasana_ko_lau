from django.contrib import admin

from .models import NewsCategory, NewsPost


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "is_featured", "published_at", "author"]
    list_filter = ["status", "category", "is_featured"]
    search_fields = ["title", "summary", "body"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["status", "is_featured"]
