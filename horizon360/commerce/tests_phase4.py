from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from cdp_core.models import Company, UserProfile, Customer, RawEvent
from commerce.models import Product, Order, Cart, CartItem

class Phase4CommerceTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.company = Company.objects.create(name="Store Corp", plan="enterprise")
        self.user = User.objects.create_user(username="store_mgr", password="password123", email="mgr@store.com")
        self.profile = UserProfile.objects.create(user=self.user, company=self.company)

        self.customer = Customer.objects.create(
            company=self.company,
            primary_email="shopper@test.com"
        )
        self.client.force_authenticate(user=self.user)

        self.p1 = Product.objects.create(company=self.company, name="Cloud Server M1", sku="SRV-M1", price=Decimal('250.00'))
        self.p2 = Product.objects.create(company=self.company, name="Storage TB1", sku="STG-TB1", price=Decimal('50.00'))

    def test_cart_management_and_checkout(self):
        # 1. Create Cart
        cart_res = self.client.post('/api/v1/commerce/carts/', {
            "customer": str(self.customer.id)
        }, format='json')
        self.assertEqual(cart_res.status_code, status.HTTP_201_CREATED)
        cart_id = cart_res.data['id']

        # 2. Add Products to Cart
        item1 = self.client.post(f'/api/v1/commerce/carts/{cart_id}/add-item/', {
            "product": self.p1.id,
            "quantity": 2,
            "unit_price": "250.00"
        }, format='json')
        self.assertEqual(item1.status_code, status.HTTP_201_CREATED)

        item2 = self.client.post(f'/api/v1/commerce/carts/{cart_id}/add-item/', {
            "product": self.p2.id,
            "quantity": 3,
            "unit_price": "50.00"
        }, format='json')
        self.assertEqual(item2.status_code, status.HTTP_201_CREATED)

        # Verify Cart Total: (2 * 250) + (3 * 50) = 500 + 150 = 650
        cart = Cart.objects.get(id=cart_id)
        self.assertEqual(cart.total_amount, Decimal('650.00'))

        # 3. Execute Checkout
        checkout_res = self.client.post(f'/api/v1/commerce/carts/{cart_id}/checkout/')
        self.assertEqual(checkout_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(checkout_res.data['status'], 'checkout_completed')
        self.assertEqual(checkout_res.data['total_amount'], 650.00)

        # Verify Cart is now empty
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)

        # Verify Order was created in DB
        order = Order.objects.get(id=checkout_res.data['order_id'])
        self.assertEqual(order.total_amount, Decimal('650.00'))
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.status, 'confirmed')

        # Verify CDP Event Emission
        event = RawEvent.objects.filter(company=self.company, event_name='order.checkout_completed').first()
        self.assertIsNotNone(event)
