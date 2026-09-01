from django.contrib import admin
from .models import Integration, IntegrationLog, WebhookSubscription, WebhookDeliveryLog

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'direction', 'status', 'company', 'created_at')
    list_filter = ('direction', 'status', 'company')
    search_fields = ('name', 'provider')

@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ('correlation_id', 'integration', 'direction', 'event_type', 'status', 'timestamp')
    list_filter = ('status', 'direction', 'company')
    search_fields = ('correlation_id', 'event_type')

class WebhookDeliveryLogInline(admin.TabularInline):
    model = WebhookDeliveryLog
    extra = 0
    readonly_fields = ('id', 'event_name', 'response_status', 'success', 'delivered_at')

@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('target_url', 'is_active', 'company', 'created_at')
    list_filter = ('is_active', 'company', 'created_at')
    search_fields = ('target_url',)
    inlines = [WebhookDeliveryLogInline]

@admin.register(WebhookDeliveryLog)
class WebhookDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscription', 'event_name', 'response_status', 'success', 'delivered_at')
    list_filter = ('success', 'event_name', 'delivered_at')
    search_fields = ('event_name', 'subscription__target_url')

