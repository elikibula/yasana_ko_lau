from django.contrib import admin

from .models import Koro, KoroDroneVideo, KoroReport


class KoroDroneVideoInline(admin.TabularInline):
    model = KoroDroneVideo
    extra = 1
    fields = ("title", "video_file", "video_url", "thumbnail", "order")


@admin.register(Koro)
class KoroAdmin(admin.ModelAdmin):
    list_display = ("name", "tikina", "is_koro_turaga", "population", "notes", "turaga_ni_koro")
    list_filter = ("tikina", "is_koro_turaga")
    search_fields = ("name", "tikina__name", "notes")
    ordering = ("tikina__number", "-is_koro_turaga", "name")
    list_editable = ("is_koro_turaga",)
    readonly_fields = ("slug",)
    inlines = [KoroDroneVideoInline]


@admin.register(KoroDroneVideo)
class KoroDroneVideoAdmin(admin.ModelAdmin):
    list_display = ("koro", "title", "order", "uploaded_at")
    list_filter = ("koro",)


@admin.register(KoroReport)
class KoroReportAdmin(admin.ModelAdmin):
    list_display = ("koro_name", "tikina", "report_type", "status", "submitted_by", "submitted_at")
    list_filter = ("tikina", "report_type", "status", "submitted_at")
    search_fields = ("koro_name", "content", "submitted_by__username", "submitted_by__first_name", "submitted_by__last_name")
