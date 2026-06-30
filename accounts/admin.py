from django.contrib import admin

from .models import TuragaProfile, UserProfile


@admin.register(TuragaProfile)
class TuragaProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "membership_type", "village", "district", "province", "appointment_date")
    list_filter = ("membership_type", "province")
    search_fields = ("user__first_name", "user__last_name", "village", "district")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "tikina", "koro", "yavusa", "phone")
    list_filter = ("role", "tikina")
    search_fields = ("user__username", "user__first_name", "user__last_name", "tikina", "koro", "yavusa")
