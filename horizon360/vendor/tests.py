from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, UserProfile, RawEvent
from vendor.models import Vendor, PurchaseOrder
from django.contrib.auth.models import User

class VendorTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.vendor_a = Vendor.objects.create(company=self.company_a, name="Vendor A", category="IT")
        self.vendor_b = Vendor.objects.create(company=self.company_b, name="Vendor B", category="Supplies")
        
        self.client = APIClient()

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Cross-tenant PO
        response = self.client.post('/api/vendor/purchase-orders/', {
            "vendor": self.vendor_b.id,
            "reference": "PO-999",
            "amount": "1000.00"
        })
        self.assertEqual(response.status_code, 400)
        
        # Valid PO
        response = self.client.post('/api/vendor/purchase-orders/', {
            "vendor": self.vendor_a.id,
            "reference": "PO-001",
            "amount": "1000.00"
        })
        self.assertEqual(response.status_code, 201)
        po_id = response.data['id']
        
        # Event generated
        events = RawEvent.objects.filter(company=self.company_a, event_name='purchase_order.created')
        self.assertEqual(events.count(), 1)
        
        # Status update event
        response = self.client.patch(f'/api/vendor/purchase-orders/{po_id}/', {
            "status": "approved"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(company=self.company_a, event_name='purchase_order.approved').count(), 1)
