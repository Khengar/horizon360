from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, Customer, UserProfile, RawEvent
from commerce.models import Product, Order, OrderItem
from django.contrib.auth.models import User

class CommerceTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="a@example.com")
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="b@example.com")
        
        self.product_a = Product.objects.create(company=self.company_a, name="Prod A", price=10.0)
        self.product_b = Product.objects.create(company=self.company_b, name="Prod B", price=20.0)
        
        self.client = APIClient()

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Test cross-tenant product creation
        response = self.client.post('/api/commerce/orders/', {
            "customer": self.customer_b.id,
            "status": "draft"
        })
        self.assertEqual(response.status_code, 400)
        
        # Valid order creation
        response = self.client.post('/api/commerce/orders/', {
            "customer": self.customer_a.id,
            "status": "draft"
        })
        self.assertEqual(response.status_code, 201)
        order_id = response.data['id']
        
        # Emits order.created
        events = RawEvent.objects.filter(company=self.company_a)
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().event_name, 'order.created')
        
        # Test cross-tenant order item
        response = self.client.post('/api/commerce/order-items/', {
            "order": order_id,
            "product": self.product_b.id,
            "quantity": 1,
            "price": "20.00"
        })
        self.assertEqual(response.status_code, 400)
        
        # Valid order item
        response = self.client.post('/api/commerce/order-items/', {
            "order": order_id,
            "product": self.product_a.id,
            "quantity": 1,
            "price": "10.00"
        })
        self.assertEqual(response.status_code, 201)
        
        # Order status events
        response = self.client.patch(f'/api/commerce/orders/{order_id}/', {
            "status": "confirmed"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(company=self.company_a, event_name='order.confirmed').count(), 1)
