from django.contrib import admin
from .models import Company, UserProfile, EventSchema, RawEvent, Customer

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'api_token', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company')
    search_fields = ('user__username', 'company__name')

@admin.register(EventSchema)
class EventSchemaAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'company')
    
@admin.register(RawEvent)
class RawEventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'company', 'processed', 'created_at')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'primary_email', 'company')
