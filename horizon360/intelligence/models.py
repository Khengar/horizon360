from django.db import models
from cdp_core.models import Company

class Insight(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='insights')
    agent_type = models.CharField(max_length=50) # e.g., 'sales', 'marketing'
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Generic entity reference (e.g., deal, customer)
    entity_type = models.CharField(max_length=50, blank=True, null=True)
    entity_id = models.CharField(max_length=50, blank=True, null=True)
    
    confidence = models.FloatField(default=1.0) # 0.0 to 1.0
    recommendation = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, default='new') # 'new', 'read', 'dismissed', 'actioned'
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.agent_type.capitalize()} Insight: {self.title}"
