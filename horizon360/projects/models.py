from django.db import models
from cdp_core.models import Company, Customer

class Project(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Project: {self.name} ({self.status})"

class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    
    def __str__(self):
        return f"Task: {self.title} ({self.status})"
