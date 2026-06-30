from django.contrib import admin

from .models import Tikina, TikinaGalleryImage, TikinaReport


class GalleryInline(admin.TabularInline):
    model = TikinaGalleryImage
    extra = 1
    fields = ["image", "caption", "order"]


@admin.register(Tikina)
class TikinaAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "island_group", "koro_count", "population", "mata_ni_tikina", "is_active"]
    list_filter = ["island_group", "is_active"]
    search_fields = ["name", "koro_turaga"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [GalleryInline]
    readonly_fields = ["koro_count"]


@admin.register(TikinaReport)
class TikinaReportAdmin(admin.ModelAdmin):
    list_display = ["tikina", "report_type", "submitted_by", "status", "submitted_at"]
    list_filter = ["status", "report_type", "tikina"]
    search_fields = ["tikina__name", "submitted_by__username"]
    readonly_fields = ["submitted_at", "updated_at"]
