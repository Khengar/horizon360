from django.db import models
from cdp_core.models import Company

class Vendor(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vendors')
    name = models.CharField(max_length=255)
    email = models.EmailField()
    category = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    reference = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO {self.reference} ({self.vendor.name})"
