from django.contrib import admin
from .models import ServiceTicket, SLAPolicy, TicketComment, KnowledgeArticle

class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 1

@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'response_time_hours', 'resolution_time_hours', 'is_active', 'company')
    list_filter = ('priority', 'is_active', 'company')

@admin.register(ServiceTicket)
class ServiceTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'customer', 'status', 'priority', 'is_sla_breached', 'sla_due_at', 'company', 'created_at')
    list_filter = ('status', 'priority', 'is_sla_breached', 'company', 'created_at')
    search_fields = ('title', 'description', 'customer__primary_email')
    inlines = [TicketCommentInline]

@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'view_count', 'company', 'created_at')
    list_filter = ('category', 'is_published', 'company')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

