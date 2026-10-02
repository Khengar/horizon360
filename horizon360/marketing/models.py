from django.db import models
from django.utils import timezone
from cdp_core.models import Company, Customer

class Campaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('digital_ads', 'Digital Ads'),
        ('web_engagement', 'Web Engagement'),
    ]
    CAMPAIGN_TYPE_CHOICES = [
        ('one_time', 'One-Time Blast'),
        ('automated', 'Automated Journey'),
        ('triggered', 'Event-Triggered'),
    ]
    BANDIT_METRIC_CHOICES = [
        ('open_rate', 'Open Rate'),
        ('click_rate', 'Click Rate'),
        ('conversion_rate', 'Conversion Rate'),
    ]

    # Tenancy & Identity
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='email')
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES, default='one_time')
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Targeting on Universal Data Model (Segments)
    segments = models.ManyToManyField('cdp_core.Segment', through='CampaignSegment', blank=True, related_name='campaigns')
    estimated_audience = models.PositiveIntegerField(default=0)
    audience_snapshot = models.JSONField(default=dict, blank=True, help_text="Frozen audience metadata at send time")

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Goal & Attribution
    goal_event = models.CharField(max_length=100, blank=True, help_text="Conversion event name e.g. deal.won")
    goal_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    attribution_window_days = models.PositiveIntegerField(default=30)

    # Contextual Multi-Armed Bandit
    bandit_enabled = models.BooleanField(default=False)
    bandit_metric = models.CharField(max_length=20, blank=True, choices=BANDIT_METRIC_CHOICES, default='click_rate')
    bandit_exploration_rate = models.FloatField(default=0.1)
    bandit_state = models.JSONField(default=dict, blank=True)
    bandit_winner_content = models.ForeignKey(
        'CampaignContent', null=True, blank=True, on_delete=models.SET_NULL, related_name='won_campaigns'
    )

    # Sender Identity
    sender_name = models.CharField(max_length=255, blank=True)
    sender_email = models.EmailField(blank=True)
    reply_to = models.EmailField(blank=True)

    # AI Feature Flags
    ai_audience_enabled = models.BooleanField(default=False)
    ai_copy_enabled = models.BooleanField(default=False)
    ai_send_time_enabled = models.BooleanField(default=False)

    # Denormalized Metrics Cache
    total_sent = models.PositiveIntegerField(default=0)
    total_delivered = models.PositiveIntegerField(default=0)
    total_opened = models.PositiveIntegerField(default=0)
    total_clicked = models.PositiveIntegerField(default=0)
    total_converted = models.PositiveIntegerField(default=0)
    total_bounced = models.PositiveIntegerField(default=0)
    total_unsubscribed = models.PositiveIntegerField(default=0)

    # Propensity Aggregates
    avg_propensity_score = models.FloatField(default=0.0)
    churn_risk_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} [{self.channel}] ({self.status})"


class CampaignSegment(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_segments')
    segment = models.ForeignKey('cdp_core.Segment', on_delete=models.CASCADE, related_name='campaign_segments')
    is_exclusion = models.BooleanField(default=False, help_text="If True, exclude this segment's audience")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('campaign', 'segment')

    def __str__(self):
        prefix = "Exclude" if self.is_exclusion else "Target"
        return f"{prefix} {self.segment.name} for {self.campaign.name}"


class CampaignContent(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='contents')
    variant_name = models.CharField(max_length=50, default='A')
    
    # Email Content
    subject = models.CharField(max_length=500, blank=True)
    preview_text = models.CharField(max_length=255, blank=True)
    body_html = models.TextField(blank=True)
    body_plain = models.TextField(blank=True)

    # SMS / Push / Digital Ads
    message_text = models.TextField(blank=True)
    cta_url = models.URLField(blank=True)
    cta_text = models.CharField(max_length=100, blank=True)

    # Multi-Armed Bandit Parameters (Thompson Sampling Beta distribution)
    bandit_alpha = models.FloatField(default=1.0, help_text="Successes + prior")
    bandit_beta = models.FloatField(default=1.0, help_text="Failures + prior")
    impressions = models.PositiveIntegerField(default=0)
    successes = models.PositiveIntegerField(default=0)
    traffic_percentage = models.PositiveIntegerField(default=100)

    # AI Generation Metadata
    ai_generated = models.BooleanField(default=False)
    ai_generation_prompt = models.TextField(blank=True)
    ai_source_references = models.JSONField(default=list, blank=True)

    # Template Reuse
    is_template = models.BooleanField(default=False)
    template_name = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['variant_name']

    def __str__(self):
        return f"{self.campaign.name} - Variant {self.variant_name}"


class CampaignRecipient(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('optimized', 'Send-Time Optimized'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('converted', 'Converted'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
        ('failed', 'Failed'),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='recipients')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='campaign_recipients')
    content_variant = models.ForeignKey(CampaignContent, on_delete=models.SET_NULL, null=True, blank=True, related_name='recipients')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaign_recipients')

    channel_address = models.CharField(max_length=512, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')

    queued_at = models.DateTimeField(auto_now_add=True)
    optimal_send_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    propensity_score = models.FloatField(default=0.0)
    churn_risk = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    conversion_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('campaign', 'customer')
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['customer', 'campaign']),
            models.Index(fields=['optimal_send_at']),
        ]

    def __str__(self):
        return f"{self.campaign.name} -> {self.customer.primary_email or self.customer.id} ({self.status})"


class CampaignEvent(models.Model):
    EVENT_TYPES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('converted', 'Converted'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
        ('complained', 'Complained'),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='events')
    recipient = models.ForeignKey(CampaignRecipient, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaign_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign', 'event_type']),
        ]

    def __str__(self):
        return f"[{self.event_type.upper()}] {self.campaign.name} at {self.created_at}"


class CampaignPropensityScore(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='propensity_scores')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='propensity_scores')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaign_propensity_scores')

    conversion_probability = models.FloatField(default=0.0)
    churn_probability = models.FloatField(default=0.0)
    optimal_send_hour = models.PositiveIntegerField(null=True, blank=True)
    optimal_send_day = models.PositiveIntegerField(null=True, blank=True)

    model_version = models.CharField(max_length=50, default='v1')
    features_snapshot = models.JSONField(default=dict, blank=True)
    scored_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('campaign', 'customer')

    def __str__(self):
        return f"Propensity: {self.customer.id} for {self.campaign.name} ({self.conversion_probability:.2f})"


class AttributionTouchpoint(models.Model):
    TOUCHPOINT_TYPES = [
        ('impression', 'Ad Impression'),
        ('email_open', 'Email Open'),
        ('email_click', 'Email Click'),
        ('sms_reply', 'SMS Reply'),
        ('web_visit', 'Web Visit'),
        ('form_submit', 'Form Submit'),
        ('conversion', 'Conversion'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='attribution_touchpoints')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='touchpoints')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='attribution_touchpoints')

    touchpoint_type = models.CharField(max_length=20, choices=TOUCHPOINT_TYPES)
    channel = models.CharField(max_length=20)

    first_touch_weight = models.FloatField(default=0.0)
    last_touch_weight = models.FloatField(default=0.0)
    linear_weight = models.FloatField(default=0.0)
    time_decay_weight = models.FloatField(default=0.0)
    position_based_weight = models.FloatField(default=0.0)

    attributed_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at']

    def __str__(self):
        return f"{self.channel} {self.touchpoint_type} by {self.customer.id} (${self.attributed_revenue})"


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


class CampaignTransaction(models.Model):
    TYPE_CHOICES = [
        ('spend', 'Campaign Spend (Expense)'),
        ('roi', 'Attributed Revenue (ROI)')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaign_transactions')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.campaign.name} - {self.transaction_type.upper()}: ${self.amount}"
