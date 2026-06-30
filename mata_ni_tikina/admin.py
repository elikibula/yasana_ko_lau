from django.contrib import admin

from .models import (
    CouncilSavingsAccount,
    FundCollectionChallenge,
    IncomeSourceItem,
    KoroUnderTikina,
    MNTReport,
    SettlementRegistrationRequest,
    Signature,
    TikinaChallengeIndicator,
    TikinaCoordinationStatus,
    TikinaDispute,
    TikinaIncomeActivity,
    TikinaSocialIndicator,
    TikinaVillageVisit,
    TreePlantingTraining,
    VagalalaSettlement,
)


class KoroUnderTikinaInline(admin.TabularInline):
    model = KoroUnderTikina
    extra = 0


class VagalalaSettlementInline(admin.TabularInline):
    model = VagalalaSettlement
    extra = 0


class SignatureInline(admin.TabularInline):
    model = Signature
    extra = 0


@admin.register(MNTReport)
class MNTReportAdmin(admin.ModelAdmin):
    list_display = ("tikina", "quarter", "year", "status", "submitted_at", "owner")
    list_filter = ("status", "quarter", "year")
    search_fields = ("tikina", "village", "full_name", "owner__username")
    inlines = [KoroUnderTikinaInline, VagalalaSettlementInline, SignatureInline]


for model in (
    SettlementRegistrationRequest,
    TikinaCoordinationStatus,
    TikinaDispute,
    TikinaSocialIndicator,
    IncomeSourceItem,
    TreePlantingTraining,
    TikinaIncomeActivity,
    CouncilSavingsAccount,
    FundCollectionChallenge,
    TikinaChallengeIndicator,
    TikinaVillageVisit,
):
    admin.site.register(model)
