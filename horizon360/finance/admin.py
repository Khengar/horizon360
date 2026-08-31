from django.contrib import admin
from .models import Invoice, Payment, JournalEntry

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('id', 'amount', 'currency', 'payment_method', 'status', 'paid_at')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'amount', 'amount_paid', 'balance_due', 'currency', 'status', 'company', 'created_at')
    list_filter = ('status', 'currency', 'company', 'created_at')
    search_fields = ('invoice_number', 'customer__primary_email')
    inlines = [PaymentInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'customer', 'amount', 'currency', 'payment_method', 'status', 'paid_at', 'company')
    list_filter = ('status', 'payment_method', 'currency', 'company', 'paid_at')
    search_fields = ('id', 'transaction_id', 'invoice__invoice_number', 'customer__primary_email')

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'entry_type', 'account_code', 'amount', 'currency', 'reference_type', 'posted_at', 'company')
    list_filter = ('entry_type', 'account_code', 'company', 'posted_at')
    search_fields = ('account_code', 'reference_id', 'description')

