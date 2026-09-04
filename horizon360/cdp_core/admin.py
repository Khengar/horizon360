from django.contrib import admin
from .models import Company, UserProfile, EventSchema, RawEvent, Customer, Account, Role, UserRole, AuditLog

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan', 'is_active', 'api_token', 'created_at')
    list_filter = ('is_active', 'plan')
    search_fields = ('name',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company')
    search_fields = ('user__username', 'company__name')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'industry', 'tier', 'annual_revenue', 'company', 'created_at')
    list_filter = ('tier', 'industry', 'company')
    search_fields = ('name', 'domain')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_system_default', 'created_at')
    list_filter = ('company', 'is_system_default')
    search_fields = ('name',)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'role', 'assigned_at')
    list_filter = ('role__company',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'entity_type', 'entity_id', 'user', 'company', 'timestamp')
    list_filter = ('action', 'entity_type', 'company', 'timestamp')
    search_fields = ('entity_id', 'entity_type', 'user__username')
    readonly_fields = ('id', 'company', 'user', 'action', 'entity_type', 'entity_id', 'diff', 'ip_address', 'timestamp')

@admin.register(EventSchema)
class EventSchemaAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'company')
    
@admin.register(RawEvent)
class RawEventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'company', 'processed', 'created_at')

from .models import Company, UserProfile, EventSchema, RawEvent, Customer, Account, Role, UserRole, AuditLog, Segment

@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_active', 'created_at')
    list_filter = ('company', 'is_active')
    search_fields = ('name',)

from .models import IdentityEdge, MergeSuggestion, UnifiedProfile, CDPPipelineStatus

@admin.register(IdentityEdge)
class IdentityEdgeAdmin(admin.ModelAdmin):
    list_display = ['identity_type', 'identity_value', 'customer', 'confidence', 'source', 'created_at']
    list_filter = ['identity_type', 'source']
    search_fields = ['identity_value']

@admin.register(MergeSuggestion)
class MergeSuggestionAdmin(admin.ModelAdmin):
    list_display = ['primary_customer', 'secondary_customer', 'confidence_score', 'status', 'created_at']
    list_filter = ['status']

@admin.register(UnifiedProfile)
class UnifiedProfileAdmin(admin.ModelAdmin):
    list_display = ['customer', 'engagement_score', 'lifecycle_stage', 'engagement_tier', 'enriched_at']
    list_filter = ['lifecycle_stage', 'engagement_tier']

@admin.register(CDPPipelineStatus)
class CDPPipelineStatusAdmin(admin.ModelAdmin):
    list_display = ['company', 'total_events_ingested', 'unified_profiles_count', 'updated_at']
