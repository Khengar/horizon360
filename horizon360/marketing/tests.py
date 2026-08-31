from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, Customer, RawEvent, UserProfile
from marketing.models import Campaign, Lead
from django.contrib.auth.models import User

class MarketingTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="alice@example.com")
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="bob@example.com")
        
        self.campaign_a = Campaign.objects.create(company=self.company_a, name="Campaign A", status="active", budget=1000)
        self.campaign_b = Campaign.objects.create(company=self.company_b, name="Campaign B", status="active", budget=2000)
        
        self.client = APIClient()

    def test_tenant_isolation_creation(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Cross-company customer rejected
        response = self.client.post('/api/marketing/leads/', {
            "customer": self.customer_b.id,
            "name": "Invalid Lead",
            "email": "invalid@example.com"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong to this company", str(response.data))

        # Cross-company campaign rejected
        response = self.client.post('/api/marketing/leads/', {
            "campaign": self.campaign_b.id,
            "name": "Invalid Lead",
            "email": "invalid@example.com"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong to this company", str(response.data))
        
        # Valid lead creation
        response = self.client.post('/api/marketing/leads/', {
            "customer": self.customer_a.id,
            "campaign": self.campaign_a.id,
            "name": "Valid Lead",
            "email": "valid@example.com"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Lead.objects.filter(company=self.company_a).count(), 1)
        self.assertEqual(RawEvent.objects.filter(event_name="lead.created").count(), 1)

    def test_lead_status_events(self):
        lead = Lead.objects.create(company=self.company_a, name="Lead A", email="a@example.com", status="new")
        self.client.force_authenticate(user=self.user_a)
        
        # Update to qualified
        response = self.client.patch(f'/api/marketing/leads/{lead.id}/', {"status": "qualified"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(event_name="lead.qualified").count(), 1)
        
        # Update to converted
        response = self.client.patch(f'/api/marketing/leads/{lead.id}/', {"status": "converted"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(event_name="lead.converted").count(), 1)

    def test_campaign_status_events(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Create draft campaign
        response = self.client.post('/api/marketing/campaigns/', {
            "name": "New Campaign",
            "status": "draft"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RawEvent.objects.filter(event_name="campaign.created").count(), 1)
        self.assertEqual(RawEvent.objects.filter(event_name="campaign.activated").count(), 0)
        
        campaign_id = response.data['id']
        
        # Update to active
        response = self.client.patch(f'/api/marketing/campaigns/{campaign_id}/', {"status": "active"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(event_name="campaign.activated").count(), 1)
