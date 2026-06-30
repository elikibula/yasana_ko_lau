from django.contrib import admin

from .models import YavusaReport


@admin.register(YavusaReport)
class YavusaReportAdmin(admin.ModelAdmin):
    list_display = ("yavusa_name", "member_count", "status", "submitted_by", "submitted_at")
    list_filter = ("status", "submitted_at")
    search_fields = ("yavusa_name", "content", "submitted_by__username")
