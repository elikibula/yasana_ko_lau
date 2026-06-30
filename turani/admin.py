from django.contrib import admin

from .models import (
    Business,
    BusinessTraining,
    CorrectionReturnee,
    CropCount,
    CulturalKnowledge,
    DisabilityCount,
    ElectricitySource,
    EvacuationCentreMaterial,
    HealthConditionCount,
    HousingCount,
    IVDPImplementationSchedule,
    IVDPProject,
    LawOffence,
    PopulationAgeGroup,
    Signature,
    TNKReport,
    ToiletType,
    TraditionalTitleStatus,
    Training,
    VillageAssetSaving,
    VillageCommittee,
    VillageMeetingDecision,
    Visit,
    WasteManagement,
    WaterCommitteeMember,
    WaterCommitteeQuestion,
    WaterSource,
)


class VisitInline(admin.TabularInline): model = Visit; extra = 0
class VillageMeetingDecisionInline(admin.TabularInline): model = VillageMeetingDecision; extra = 0
class VillageCommitteeInline(admin.TabularInline): model = VillageCommittee; extra = 0
class LawOffenceInline(admin.TabularInline): model = LawOffence; extra = 0
class CorrectionReturneeInline(admin.TabularInline): model = CorrectionReturnee; extra = 0
class TrainingInline(admin.StackedInline): model = Training; extra = 0
class PopulationAgeGroupInline(admin.TabularInline): model = PopulationAgeGroup; extra = 0
class HousingCountInline(admin.TabularInline): model = HousingCount; extra = 0
class WaterSourceInline(admin.TabularInline): model = WaterSource; extra = 0
class WaterCommitteeQuestionInline(admin.TabularInline): model = WaterCommitteeQuestion; extra = 0
class WaterCommitteeMemberInline(admin.TabularInline): model = WaterCommitteeMember; extra = 0
class WasteManagementInline(admin.StackedInline): model = WasteManagement; extra = 0; max_num = 1
class ToiletTypeInline(admin.TabularInline): model = ToiletType; extra = 0
class ElectricitySourceInline(admin.TabularInline): model = ElectricitySource; extra = 0
class HealthConditionCountInline(admin.StackedInline): model = HealthConditionCount; extra = 0
class DisabilityCountInline(admin.StackedInline): model = DisabilityCount; extra = 0
class CropCountInline(admin.TabularInline): model = CropCount; extra = 0
class IVDPProjectInline(admin.StackedInline): model = IVDPProject; extra = 0
class IVDPImplementationScheduleInline(admin.TabularInline): model = IVDPImplementationSchedule; extra = 0
class BusinessInline(admin.TabularInline): model = Business; extra = 0
class BusinessTrainingInline(admin.TabularInline): model = BusinessTraining; extra = 0
class VillageAssetSavingInline(admin.TabularInline): model = VillageAssetSaving; extra = 0
class EvacuationCentreMaterialInline(admin.TabularInline): model = EvacuationCentreMaterial; extra = 0
class TraditionalTitleStatusInline(admin.TabularInline): model = TraditionalTitleStatus; extra = 0
class CulturalKnowledgeInline(admin.TabularInline): model = CulturalKnowledge; extra = 0
class SignatureInline(admin.TabularInline): model = Signature; extra = 0


@admin.register(TNKReport)
class TNKReportAdmin(admin.ModelAdmin):
    list_display = ["village", "district", "quarter", "year", "status", "submitted_at", "household_count", "village_meetings_count", "created_at"]
    list_filter = ["quarter", "year", "province", "status"]
    search_fields = ["village", "district", "village_headman_name", "owner__username"]
    readonly_fields = ["created_at", "updated_at", "submitted_at"]
    inlines = [
        VisitInline, VillageMeetingDecisionInline, VillageCommitteeInline, PopulationAgeGroupInline,
        HousingCountInline, WaterSourceInline, WaterCommitteeQuestionInline, WaterCommitteeMemberInline,
        ToiletTypeInline, ElectricitySourceInline, LawOffenceInline, CorrectionReturneeInline,
        TrainingInline, HealthConditionCountInline, DisabilityCountInline, CropCountInline,
        IVDPProjectInline, IVDPImplementationScheduleInline, BusinessTrainingInline, BusinessInline, VillageAssetSavingInline,
        EvacuationCentreMaterialInline, TraditionalTitleStatusInline, CulturalKnowledgeInline,
        SignatureInline, WasteManagementInline,
    ]
