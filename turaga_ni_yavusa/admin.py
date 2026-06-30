from django.contrib import admin

from .models import Signature, TNYReport


class SignatureInline(admin.TabularInline):
    model = Signature
    extra = 0


@admin.register(TNYReport)
class TNYReportAdmin(admin.ModelAdmin):
    list_display = ("yavusa", "vanua", "quarter", "year", "status", "submitted_at", "owner")
    list_filter = ("status", "quarter", "year")
    search_fields = ("yavusa", "vanua", "mataqali", "tokatoka", "full_name", "owner__username")
    inlines = [SignatureInline]
