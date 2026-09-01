from django.db import models
from cdp_core.models import Company, Customer

class Campaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.status})"


class Lead(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('lost', 'Lost')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leads')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    lead_score = models.PositiveIntegerField(default=0, help_text="Behavioral and profile qualification score")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate_score(self, persist=True):
        score = 0
        if self.email and '@' in self.email:
            score += 20
        if self.phone:
            score += 15
        if self.company_name:
            score += 25
        if self.customer and self.customer.timeline:
            score += min(40, len(self.customer.timeline) * 10)
        self.lead_score = score
        if score >= 60 and self.status == 'new':
            self.status = 'qualified'
        if persist:
            self.save(update_fields=['lead_score', 'status'])
        return self.lead_score

    def __str__(self):
        return f"Lead: {self.name} ({self.lead_score} pts) - {self.status}"

