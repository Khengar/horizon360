from django.db import models
from django.contrib.auth.models import User
from cdp_core.models import Customer, Company
from django.db.models.signals import post_save
from django.dispatch import receiver

class Contact(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='contact')
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

    def save(self, *args, **kwargs):
        if not self.company and self.customer:
            self.company = self.customer.company
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Contact: {self.primary_email or self.primary_phone or self.customer.id}"


class Deal(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    STAGE_CHOICES = [
        ('lead', 'Lead'),
        ('qualified', 'Qualified'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]
    title = models.CharField(max_length=255, default='New Deal')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='deals', null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='deals', null=True, blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='lead')
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    expected_close_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.company:
            if self.contact and self.contact.company != self.company:
                raise ValidationError("Deal company must match Contact company.")
            if self.customer and self.customer.company != self.company:
                raise ValidationError("Deal company must match Customer company.")
        if self.contact and self.customer and self.contact.customer != self.customer:
            raise ValidationError("Deal contact must belong to the Deal customer.")

    def save(self, *args, **kwargs):
        if not self.customer and self.contact:
            self.customer = self.contact.customer
        if not self.company:
            if self.customer:
                self.company = self.customer.company
            elif self.contact:
                self.company = self.contact.company
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
                    "value": float(self.value)
                },
                processed=False
            )
            process_event_task.delay(raw_event.id)

    def __str__(self):
        return f"Deal for {self.contact or self.customer} - {self.get_stage_display()} - ${self.value}"

@receiver(post_save, sender=Customer)
def create_contact_for_customer(sender, instance, created, **kwargs):
    if created:
        Contact.objects.get_or_create(customer=instance, company=instance.company)

