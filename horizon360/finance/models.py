import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from cdp_core.models import Company, Customer
from crm.models import Deal

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='finance_products')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('issued', 'Issued'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled')
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    
    invoice_number = models.CharField(max_length=50)
    currency = models.CharField(max_length=3, default='USD')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issued_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def balance_due(self):
        return max(Decimal('0.00'), self.amount - (self.amount_paid or Decimal('0.00')))

    def __str__(self):
        return f"{self.invoice_number} ({self.currency} {self.amount}) - {self.status}"

class LineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='line_items')
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else self.description}"

class Payment(models.Model):
    METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer / Wire'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash'),
        ('other', 'Other')
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='credit_card')
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    paid_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_payment = Payment.objects.get(pk=self.pk)
                old_status = old_payment.status
            except Payment.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Automated Invoice Reconciliation
        if self.invoice and self.status == 'completed' and (is_new or old_status != 'completed'):
            completed_payments = self.invoice.payments.filter(status='completed')
            total_paid = sum((p.amount for p in completed_payments), Decimal('0.00'))
            self.invoice.amount_paid = total_paid
            
            if total_paid >= self.invoice.amount:
                self.invoice.status = 'paid'
            elif total_paid > 0:
                self.invoice.status = 'partially_paid'
            self.invoice.save(update_fields=['amount_paid', 'status'])

            # Automatically create Double-Entry General Ledger records
            JournalEntry.objects.create(
                company=self.company,
                entry_type='debit',
                account_code='1010_CASH',
                amount=self.amount,
                currency=self.currency,
                reference_type='payment',
                reference_id=str(self.id),
                description=f"Cash receipt for Invoice {self.invoice.invoice_number}"
            )
            JournalEntry.objects.create(
                company=self.company,
                entry_type='credit',
                account_code='1200_ACCOUNTS_RECEIVABLE',
                amount=self.amount,
                currency=self.currency,
                reference_type='payment',
                reference_id=str(self.id),
                description=f"AR reduction for Invoice {self.invoice.invoice_number}"
            )

            # Emit CDP Event
            from cdp_core.models import RawEvent
            from cdp_core.tasks import process_event_task
            raw_event = RawEvent.objects.create(
                company=self.company,
                customer=self.customer,
                event_name='payment.completed',
                raw_payload={
                    "payment_id": str(self.id),
                    "invoice_id": self.invoice.id,
                    "invoice_number": self.invoice.invoice_number,
                    "amount": float(self.amount),
                    "currency": self.currency,
                    "payment_method": self.payment_method,
                    "transaction_id": self.transaction_id
                },
                processed=False
            )
            process_event_task.delay(raw_event.id)

    def __str__(self):
        return f"Payment {self.id}: {self.currency} {self.amount} ({self.status})"

class Expense(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Expense: {self.description} ({self.amount} {self.currency}) - {self.status}"

class JournalEntry(models.Model):
    ENTRY_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    entry_number = models.CharField(max_length=50, blank=True)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    account_code = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    posted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return f"[{self.entry_type.upper()}] {self.account_code}: {self.currency} {self.amount} ({self.reference_type})"


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('earn', 'Earn (Credit)'),
        ('loss', 'Loss (Debit)')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.transaction_type.upper()}: {self.description} - {self.amount}"

