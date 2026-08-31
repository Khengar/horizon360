from django.contrib import admin
from .models import Contact, Deal, PipelineStage, Quote, QuoteItem, Activity
import json
from django.utils.safestring import mark_safe

@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'probability', 'is_won', 'is_lost', 'company')
    list_filter = ('company', 'is_won', 'is_lost')
    ordering = ('order',)

class DealInline(admin.TabularInline):
    model = Deal
    extra = 1

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_primary_email', 'get_primary_phone', 'account', 'owner', 'created_at')
    readonly_fields = ('get_primary_email', 'get_primary_phone', 'get_timeline_display')
    list_filter = ('company', 'account')
    inlines = [DealInline]
    
    fieldsets = (
        ('CDP Data (Read-Only)', {
            'fields': ('get_primary_email', 'get_primary_phone', 'get_timeline_display')
        }),
        ('CRM Data', {
            'fields': ('customer', 'account', 'owner', 'notes')
        }),
    )

    def get_primary_email(self, obj):
        return obj.primary_email
    get_primary_email.short_description = 'Primary Email'

    def get_primary_phone(self, obj):
        return obj.primary_phone
    get_primary_phone.short_description = 'Primary Phone'

    def get_timeline_display(self, obj):
        if not obj.timeline:
            return "No timeline events."
        
        formatted_json = json.dumps(obj.timeline, indent=4)
        return mark_safe(f'<pre style="white-space: pre-wrap; font-family: monospace;">{formatted_json}</pre>')
    get_timeline_display.short_description = 'Chronological Timeline'


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'account', 'contact', 'stage', 'probability', 'value', 'health_score', 'stalled', 'created_at')
    list_filter = ('stage', 'forecast_category', 'stalled', 'company', 'account', 'created_at')
    search_fields = ('title', 'contact__customer__primary_email', 'account__name')


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('quote_number', 'deal', 'account', 'status', 'total_amount', 'valid_until', 'company')
    list_filter = ('status', 'company', 'created_at')
    search_fields = ('quote_number', 'deal__title', 'account__name')
    inlines = [QuoteItemInline]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity_type', 'deal', 'account', 'customer', 'user', 'performed_at')
    list_filter = ('activity_type', 'company', 'performed_at')
    search_fields = ('title', 'description', 'deal__title', 'account__name')


