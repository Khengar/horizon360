import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from cdp_core.models import Company, Customer

class SLAPolicy(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sla_policies')
    name = models.CharField(max_length=100)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    response_time_hours = models.PositiveIntegerField(default=24, help_text="Target first response time in hours")
    resolution_time_hours = models.PositiveIntegerField(default=72, help_text="Target ticket resolution time in hours")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'priority')

    def __str__(self):
        return f"SLA: {self.name} [{self.priority.upper()}] ({self.resolution_time_hours}h)"


class ServiceTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_on_customer', 'Waiting on Customer'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='service_tickets')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='service_tickets')
    sla_policy = models.ForeignKey(SLAPolicy, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='low')
    
    is_sla_breached = models.BooleanField(default=False)
    first_responded_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    sla_due_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def check_sla_status(self):
        now = timezone.now()
        if self.sla_due_at and not self.resolved_at and now > self.sla_due_at:
            self.is_sla_breached = True
            return True
        return self.is_sla_breached

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Auto-assign SLA policy if not set
        if not self.sla_policy and self.company:
            self.sla_policy = SLAPolicy.objects.filter(company=self.company, priority=self.priority, is_active=True).first()
        
        # Calculate sla_due_at if policy assigned
        if not self.sla_due_at and self.sla_policy:
            base_time = self.created_at if self.created_at else timezone.now()
            self.sla_due_at = base_time + timedelta(hours=self.sla_policy.resolution_time_hours)

        if self.status in ['resolved', 'closed'] and not self.resolved_at:
            self.resolved_at = timezone.now()

        self.check_sla_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket #{self.id}: {self.title} ({self.status})"


class TicketComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal private note visible only to support agents")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update first_responded_at if author is an agent and not internal
        if not self.ticket.first_responded_at and not self.is_internal:
            self.ticket.first_responded_at = timezone.now()
            self.ticket.save(update_fields=['first_responded_at'])

    def __str__(self):
        prefix = "[INTERNAL] " if self.is_internal else ""
        return f"{prefix}Comment on #{self.ticket.id} by {self.author or 'System'}"


class KnowledgeArticle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='knowledge_articles')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    category = models.CharField(max_length=100, default='General')
    content = models.TextField(help_text="Markdown formatted article content")
    is_published = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('company', 'slug')

    def __str__(self):
        return f"KB: {self.title} ({self.category})"



class ServiceEntitlement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='service_entitlements')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='service_entitlements')
    
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    purchase_date = models.DateTimeField(default=timezone.now)
    
    # Feedback System
    feedback_rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1 to 5 stars")
    feedback_text = models.TextField(null=True, blank=True)
    
    # Guarantee & Returns
    guarantee_period = models.CharField(max_length=100, help_text="e.g. '12 Months', '2 Years'")
    guarantee_end_date = models.DateTimeField(null=True, blank=True)
    return_issued = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"{self.product_name} - {self.customer.user.email}"
