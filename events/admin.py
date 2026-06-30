from django.contrib import admin

from .models import Event, EventCategory, EventRSVP


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "start_date", "location", "tikina"]
    list_filter = ["status", "category", "tikina"]
    search_fields = ["title", "description", "location"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ["event", "user", "attending", "created_at"]
    list_filter = ["attending", "event"]
