from django.contrib import admin
from .models import (
    Campaign, CampaignSegment, CampaignContent, CampaignRecipient,
    CampaignEvent, CampaignPropensityScore, AttributionTouchpoint,
    Lead, CampaignTransaction
)

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'status', 'budget', 'estimated_audience', 'total_sent', 'total_opened', 'company', 'created_at')
    list_filter = ('status', 'channel', 'campaign_type', 'company')
    search_fields = ('name', 'description')

@admin.register(CampaignSegment)
class CampaignSegmentAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'segment', 'is_exclusion', 'created_at')
    list_filter = ('is_exclusion',)

@admin.register(CampaignContent)
class CampaignContentAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'variant_name', 'subject', 'impressions', 'successes', 'is_template')
    list_filter = ('is_template', 'ai_generated')

@admin.register(CampaignRecipient)
class CampaignRecipientAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'customer', 'status', 'channel_address', 'propensity_score', 'sent_at', 'opened_at')
    list_filter = ('status', 'churn_risk')
    search_fields = ('channel_address', 'customer__primary_email')

@admin.register(CampaignEvent)
class CampaignEventAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'event_type', 'recipient', 'created_at')
    list_filter = ('event_type',)

@admin.register(CampaignPropensityScore)
class CampaignPropensityScoreAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'customer', 'conversion_probability', 'churn_probability', 'optimal_send_hour', 'scored_at')
    list_filter = ('model_version',)

@admin.register(AttributionTouchpoint)
class AttributionTouchpointAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'customer', 'channel', 'touchpoint_type', 'attributed_revenue', 'occurred_at')
    list_filter = ('channel', 'touchpoint_type')

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company_name', 'lead_score', 'status', 'campaign', 'company')
    list_filter = ('status', 'company')
    search_fields = ('name', 'email', 'company_name')

@admin.register(CampaignTransaction)
class CampaignTransactionAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'transaction_type', 'amount', 'date', 'company')
    list_filter = ('transaction_type', 'company')
    search_fields = ('description', 'campaign__name')
