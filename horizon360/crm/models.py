from django.db import models
from django.contrib.auth.models import User
from cdp_core.models import Customer, Company

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

    def __str__(self):
        return f"Contact: {self.primary_email or self.primary_phone or self.customer.id}"


class Deal(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    STAGE_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='deals')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deal for {self.contact} - {self.get_stage_display()} - ${self.value}"
