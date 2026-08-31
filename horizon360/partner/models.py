from django.db import models
from cdp_core.models import Company, Customer

class Partner(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='partners')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='as_partner')
    name = models.CharField(max_length=255)
    email = models.EmailField()
    type = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class PartnerOpportunity(models.Model):
    STAGE_CHOICES = [
        ('open', 'Open'),
        ('won', 'Won'),
        ('lost', 'Lost')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='partner_opportunities')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='opportunities')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='partner_opportunities')
    name = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.partner.name})"
