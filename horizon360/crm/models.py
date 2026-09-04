import uuid
from django.db import models
from django.contrib.auth.models import User
from cdp_core.models import Customer, Company, Account
from django.db.models.signals import post_save
from django.dispatch import receiver

class PipelineStage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='pipeline_stages')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    probability = models.PositiveIntegerField(default=10, help_text="Default win probability percentage 0-100")
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)
    color_code = models.CharField(max_length=20, default='#3B82F6')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.probability}%) - {self.company.name}"


class Contact(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='contact')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def primary_email(self):
        return self.customer.primary_email

    @property
    def primary_phone(self):
        return self.customer.primary_phone

    @property
    def timeline(self):
        return self.customer.timeline

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.company and self.customer and self.customer.company != self.company:
            raise ValidationError("Contact company must match Customer company.")
        if self.company and self.account and self.account.company != self.company:
            raise ValidationError("Contact company must match Account company.")

    def save(self, *args, **kwargs):
        if not self.company and self.customer:
            self.company = self.customer.company
        if not self.account and self.customer and self.customer.account:
            self.account = self.customer.account
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Contact: {self.primary_email or self.primary_phone or self.customer.id}"


class Deal(models.Model):
    STAGE_CHOICES = [
        ('visitor', 'Visitor'),
        ('lead', 'Lead'),
        ('opportunity', 'Opportunity'),
        ('proposal', 'Proposal'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]
    FORECAST_CHOICES = [
        ('pipeline', 'Pipeline'),
        ('best_case', 'Best Case'),
        ('commit', 'Commit'),
        ('closed', 'Closed'),
        ('omitted', 'Omitted'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255, default='New Deal')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='deals', null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='deals', null=True, blank=True)
    pipeline_stage = models.ForeignKey(PipelineStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_deals')
    
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='lead')
    probability = models.PositiveIntegerField(default=10, help_text="Estimated close probability percentage 0-100")
    forecast_category = models.CharField(max_length=20, choices=FORECAST_CHOICES, default='pipeline')
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    health_score = models.IntegerField(default=100, help_text="Deterministic deal health score (0-100)")
    stalled = models.BooleanField(default=False)
    lost_reason = models.TextField(blank=True)
    expected_close_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def weighted_value(self):
        return round((float(self.value) * (self.probability or 0)) / 100.0, 2)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.company:
            if self.contact and self.contact.company != self.company:
                raise ValidationError("Deal company must match Contact company.")
            if self.customer and self.customer.company != self.company:
                raise ValidationError("Deal company must match Customer company.")
            if self.account and self.account.company != self.company:
                raise ValidationError("Deal company must match Account company.")
        if self.contact and self.customer and self.contact.customer != self.customer:
            raise ValidationError("Deal contact must belong to the Deal customer.")

    def save(self, *args, **kwargs):
        if not self.customer and self.contact:
            self.customer = self.contact.customer
        if not self.account and self.contact and self.contact.account:
            self.account = self.contact.account
        elif not self.account and self.customer and self.customer.account:
            self.account = self.customer.account

        if not self.company:
            if self.customer:
                self.company = self.customer.company
            elif self.contact:
                self.company = self.contact.company
            elif self.account:
                self.company = self.account.company

        # Default probability from pipeline_stage if assigned and probability not explicitly set
        if self.pipeline_stage and not self.probability:
            self.probability = self.pipeline_stage.probability

        # Update forecast category for won/lost
        if self.stage == 'won':
            self.forecast_category = 'closed'
            self.probability = 100
        elif self.stage == 'lost':
            self.forecast_category = 'omitted'
            self.probability = 0

        self.clean()
        
        is_new = self.pk is None
        old_stage = None
        if not is_new:
            old_deal = Deal.objects.get(pk=self.pk)
            old_stage = old_deal.stage
            
        super().save(*args, **kwargs)
        
        # Emit event if stage changed
        if is_new or old_stage != self.stage:
            from cdp_core.models import RawEvent
            from cdp_core.tasks import process_event_task
            
            event_name = f'deal.{self.stage}' if self.stage in ['won', 'lost'] else 'deal.stage_changed'
            
            raw_event = RawEvent.objects.create(
                company=self.company,
                customer=self.customer,
                event_name=event_name,
                raw_payload={
                    "deal_id": self.id,
                    "title": self.title,
                    "stage": self.stage,
                    "value": float(self.value),
                    "probability": self.probability
                },
                processed=False
            )
            process_event_task.delay(raw_event.id)

        # Trigger cross-BIOM orchestration when deal is won
        if self.stage == 'won' and old_stage != 'won':
            from crm.tasks import run_deal_won_orchestration
            run_deal_won_orchestration.delay(self.id)

    def __str__(self):
        return f"Deal: {self.title} - {self.get_stage_display()} - ${self.value}"


from decimal import Decimal

class Quote(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='quotes')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='quotes', null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotes')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotes')
    
    quote_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def recalculate_totals(self):
        items = list(self.items.all())
        subtotal = sum((item.total_price for item in items), Decimal('0.00'))
        discount = subtotal * (Decimal(str(self.discount_percent or 0)) / Decimal('100.0'))
        taxable = subtotal - discount
        tax = taxable * (Decimal(str(self.tax_percent or 0)) / Decimal('100.0'))
        self.subtotal = round(subtotal, 2)
        self.total_amount = round(taxable + tax, 2)
        self.save(update_fields=['subtotal', 'total_amount'])

    def __str__(self):
        return f"{self.quote_number} (${self.total_amount}) - {self.status}"


class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        gross = Decimal(str(self.unit_price)) * Decimal(str(self.quantity))
        self.total_price = max(Decimal('0.00'), gross - Decimal(str(self.discount_amount or 0)))
        super().save(*args, **kwargs)
        self.quote.recalculate_totals()

    def __str__(self):
        return f"{self.quantity}x {self.product_name} - ${self.total_price}"



class Activity(models.Model):
    ACTIVITY_CHOICES = [
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('note', 'Note'),
        ('task', 'Task'),
        ('system', 'System Event'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='activities')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='note')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    performed_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f"[{self.activity_type.upper()}] {self.title} ({self.performed_at.strftime('%Y-%m-%d')})"


@receiver(post_save, sender=Customer)
def create_contact_for_customer(sender, instance, created, **kwargs):
    if created:
        Contact.objects.get_or_create(customer=instance, company=instance.company, account=instance.account)



