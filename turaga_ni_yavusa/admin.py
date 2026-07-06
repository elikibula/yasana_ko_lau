from django.contrib import admin

from .models import Signature, TNYReport


class SignatureInline(admin.TabularInline):
    model = Signature
    extra = 0


@admin.register(TNYReport)
class TNYReportAdmin(admin.ModelAdmin):
    list_display = ("yavusa", "vanua", "koro", "tikina", "quarter", "year", "status", "submitted_at", "owner")
    list_filter = ("status", "quarter", "year")
    search_fields = ("yavusa", "vanua", "mataqali", "tokatoka", "full_name", "phone_number", "email", "koro", "tikina", "owner__username")
    inlines = [SignatureInline]
