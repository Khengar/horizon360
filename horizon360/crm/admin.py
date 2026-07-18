from django.contrib import admin
from .models import Contact, Deal
import json
from django.utils.safestring import mark_safe

class DealInline(admin.TabularInline):
    model = Deal
    extra = 1

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_primary_email', 'get_primary_phone', 'owner', 'created_at')
    readonly_fields = ('get_primary_email', 'get_primary_phone', 'get_timeline_display')
    inlines = [DealInline]
    
    fieldsets = (
        ('CDP Data (Read-Only)', {
            'fields': ('get_primary_email', 'get_primary_phone', 'get_timeline_display')
        }),
        ('CRM Data', {
            'fields': ('customer', 'owner', 'notes')
        }),
    )

    def get_primary_email(self, obj):
        return obj.primary_email
    get_primary_email.short_description = 'Primary Email'

    def get_primary_phone(self, obj):
        return obj.primary_phone
    get_primary_phone.short_description = 'Primary Phone'

    def get_timeline_display(self, obj):
        # Format the JSON timeline beautifully for operations team
        if not obj.timeline:
            return "No timeline events."
        
        formatted_json = json.dumps(obj.timeline, indent=4)
        return mark_safe(f'<pre style="white-space: pre-wrap; font-family: monospace;">{formatted_json}</pre>')
    get_timeline_display.short_description = 'Chronological Timeline'


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact', 'stage', 'value', 'created_at')
    list_filter = ('stage', 'created_at')
    search_fields = ('contact__customer__primary_email',)
