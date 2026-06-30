from django.contrib import admin

from .models import ContactMessage, News


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "published_at", "updated_at")
    list_filter = ("is_published", "published_at")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "summary", "body")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "created_at")
    list_filter = ("created_at",)
    search_fields = ("subject", "name", "email", "message")
