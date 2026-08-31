from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, Customer, UserProfile, RawEvent
from partner.models import Partner, PartnerOpportunity
from django.contrib.auth.models import User

class PartnerTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="a@example.com")
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="b@example.com")
        
        self.partner_a = Partner.objects.create(company=self.company_a, name="Partner A")
        self.partner_b = Partner.objects.create(company=self.company_b, name="Partner B")
        
        self.client = APIClient()

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Test cross-tenant partner creation
        response = self.client.post('/api/partner/partners/', {
            "customer": self.customer_b.id,
            "name": "Invalid Partner",
            "type": "Reseller"
        })
        self.assertEqual(response.status_code, 400)
        
        # Valid partner creation
        response = self.client.post('/api/partner/partners/', {
            "customer": self.customer_a.id,
            "name": "Valid Partner",
            "email": "partner@example.com",
            "type": "Reseller"
        })
        self.assertEqual(response.status_code, 201)
        partner_id = response.data['id']
        
        # Emits partner.created
        events = RawEvent.objects.filter(company=self.company_a, event_name='partner.created')
        self.assertEqual(events.count(), 1)
        
        # Test cross-tenant opportunity
        response = self.client.post('/api/partner/opportunities/', {
            "partner": self.partner_b.id,
            "name": "Invalid Opp",
            "value": "1000.00"
        })
        self.assertEqual(response.status_code, 400)
        
        # Valid opportunity
        response = self.client.post('/api/partner/opportunities/', {
            "partner": partner_id,
            "customer": self.customer_a.id,
            "name": "Valid Opp",
            "value": "1000.00"
        })
        self.assertEqual(response.status_code, 201)
        opp_id = response.data['id']
        
        # Opportunity status events
        response = self.client.patch(f'/api/partner/opportunities/{opp_id}/', {
            "stage": "won"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(company=self.company_a, event_name='partner_opportunity.won').count(), 1)
