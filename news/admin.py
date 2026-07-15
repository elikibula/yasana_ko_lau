from django.contrib import admin

from .models import NewsCategory, NewsPhoto, NewsPost


class NewsPhotoInline(admin.TabularInline):
    model = NewsPhoto
    extra = 1


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ["title", "news_type", "category", "status", "is_featured", "published_at", "author"]
    list_filter = ["news_type", "status", "category", "is_featured", "published_at"]
    search_fields = ["title", "summary", "body"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["status", "is_featured"]
    inlines = [NewsPhotoInline]
