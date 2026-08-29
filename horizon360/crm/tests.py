from django.test import TestCase
from django.core.exceptions import ValidationError
from cdp_core.models import Company, Customer
from crm.models import Contact, Deal

class CRMIntegrityTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="a@test.com")
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="b@test.com")

    def test_contact_customer_integrity(self):
        contact = Contact(company=self.company_a, customer=self.customer_b)
        with self.assertRaises(ValidationError):
            contact.clean()

    def test_deal_customer_integrity(self):
        contact_a = Contact.objects.get(customer=self.customer_a)
        deal = Deal(company=self.company_b, customer=self.customer_a, contact=contact_a)
        with self.assertRaises(ValidationError):
            deal.clean()

    def test_deal_contact_integrity(self):
        contact_a = Contact.objects.get(customer=self.customer_a)
        deal = Deal(company=self.company_b, customer=self.customer_b, contact=contact_a)
        with self.assertRaises(ValidationError):
            deal.clean()

    def test_deal_contact_customer_match(self):
        contact_b = Contact.objects.get(customer=self.customer_b)
        deal = Deal(company=self.company_a, customer=self.customer_a, contact=contact_b)
        with self.assertRaises(ValidationError):
            deal.clean()

    def test_tenant_api_isolation(self):
        from rest_framework.test import APIClient
        from django.contrib.auth.models import User
        from cdp_core.models import UserProfile
        
        user_a = User.objects.create_user(username="user_a", password="password")
        UserProfile.objects.create(user=user_a, company=self.company_a)
        
        user_b = User.objects.create_user(username="user_b", password="password")
        UserProfile.objects.create(user=user_b, company=self.company_b)
        
        # Create records
        contact_a = Contact.objects.get(customer=self.customer_a)
        deal_a = Deal.objects.create(company=self.company_a, customer=self.customer_a, contact=contact_a, value=100)
        
        contact_b = Contact.objects.get(customer=self.customer_b)
        deal_b = Deal.objects.create(company=self.company_b, customer=self.customer_b, contact=contact_b, value=200)
        
        client = APIClient()
        client.force_authenticate(user=user_a)
        
        res_deals = client.get('/api/crm/deals/')
        self.assertEqual(res_deals.status_code, 200)
        self.assertEqual(len(res_deals.data), 1)
        self.assertEqual(res_deals.data[0]['id'], deal_a.id)

        res_contacts = client.get('/api/crm/contacts/')
        self.assertEqual(res_contacts.status_code, 200)
        self.assertEqual(len(res_contacts.data), 1)
        self.assertEqual(res_contacts.data[0]['id'], contact_a.id)

    def test_unauthenticated_deal_access(self):
        from rest_framework.test import APIClient
        client = APIClient()
        res = client.get('/api/crm/deals/')
        self.assertEqual(res.status_code, 403)

    def test_deal_creation(self):
        from rest_framework.test import APIClient
        from django.contrib.auth.models import User
        from cdp_core.models import UserProfile
        
        user_a = User.objects.create_user(username="user_a_create", password="password")
        UserProfile.objects.create(user=user_a, company=self.company_a)
        
        client = APIClient()
        client.force_authenticate(user=user_a)
        
        payload = {
            "title": "New Big Deal",
            "customer": self.customer_a.id,
            "value": 1000.00,
            "stage": "qualified"
        }
        res = client.post('/api/crm/deals/', payload)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['title'], "New Big Deal")
        self.assertEqual(res.data['stage'], "qualified")

    def test_deal_creation_cross_company_rejected(self):
        from rest_framework.test import APIClient
        from django.contrib.auth.models import User
        from cdp_core.models import UserProfile
        
        user_a = User.objects.create_user(username="user_a_cross", password="password")
        UserProfile.objects.create(user=user_a, company=self.company_a)
        
        client = APIClient()
        client.force_authenticate(user=user_a)
        
        payload = {
            "title": "Stolen Deal",
            "customer": self.customer_b.id,
            "value": 500.00,
            "stage": "lead"
        }
        res = client.post('/api/crm/deals/', payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn('customer', res.data)

    def test_deal_stage_transition_persists(self):
        from rest_framework.test import APIClient
        from django.contrib.auth.models import User
        from cdp_core.models import UserProfile
        
        user_a = User.objects.create_user(username="user_a_update", password="password")
        UserProfile.objects.create(user=user_a, company=self.company_a)
        
        contact_a = Contact.objects.get(customer=self.customer_a)
        deal = Deal.objects.create(company=self.company_a, customer=self.customer_a, contact=contact_a, title="Test Deal", stage="lead", value=100)
        
        client = APIClient()
        client.force_authenticate(user=user_a)
        
        res = client.patch(f'/api/crm/deals/{deal.id}/', {"stage": "won"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['stage'], "won")
        
        deal.refresh_from_db()
        self.assertEqual(deal.stage, "won")

class DealEventIdempotencyTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Idempotency Corp")
        self.customer = Customer.objects.create(company=self.company, primary_email="idem@test.com")
        self.contact = Contact.objects.get(customer=self.customer)

    def test_new_deal_creates_exactly_one_event(self):
        from cdp_core.models import RawEvent
        initial_count = RawEvent.objects.count()
        Deal.objects.create(company=self.company, customer=self.customer, contact=self.contact, title="Idem Deal", stage="lead", value=100)
        self.assertEqual(RawEvent.objects.count(), initial_count + 1)
        event = RawEvent.objects.latest('id')
        self.assertEqual(event.event_name, 'deal.stage_changed')

    def test_stage_change_creates_exactly_one_event(self):
        from cdp_core.models import RawEvent
        deal = Deal.objects.create(company=self.company, customer=self.customer, contact=self.contact, title="Idem Deal", stage="lead", value=100)
        initial_count = RawEvent.objects.count()
        
        deal.stage = "qualified"
        deal.save()
        
        self.assertEqual(RawEvent.objects.count(), initial_count + 1)
        event = RawEvent.objects.latest('id')
        self.assertEqual(event.event_name, 'deal.stage_changed')
        self.assertEqual(event.raw_payload['stage'], 'qualified')

    def test_transition_to_won_creates_deal_won_event(self):
        from cdp_core.models import RawEvent
        deal = Deal.objects.create(company=self.company, customer=self.customer, contact=self.contact, title="Idem Deal", stage="negotiation", value=100)
        initial_count = RawEvent.objects.count()
        
        deal.stage = "won"
        deal.save()
        
        self.assertEqual(RawEvent.objects.count(), initial_count + 1)
        event = RawEvent.objects.latest('id')
        self.assertEqual(event.event_name, 'deal.won')

    def test_saving_unchanged_deal_does_not_create_event(self):
        from cdp_core.models import RawEvent
        deal = Deal.objects.create(company=self.company, customer=self.customer, contact=self.contact, title="Idem Deal", stage="won", value=100)
        initial_count = RawEvent.objects.count()
        
        # Save without changing stage
        deal.value = 200
        deal.save()
        
        # Count should remain the same
        self.assertEqual(RawEvent.objects.count(), initial_count)

    def test_order_completed_creates_deal_and_won_event(self):
        from cdp_core.models import RawEvent
        from cdp_core.tasks import process_event_task
        
        # Simulate order.completed
        raw_event = RawEvent.objects.create(
            company=self.company,
            customer=self.customer,
            event_name='order.completed',
            raw_payload={"email": "idem@test.com", "amount": 500},
            processed=False
        )
        
        initial_deal_count = Deal.objects.count()
        initial_event_count = RawEvent.objects.count()
        
        process_event_task(raw_event.id)
        
        # One deal should be created
        self.assertEqual(Deal.objects.count(), initial_deal_count + 1)
        
        # The deal creation should have spawned exactly one deal.won event
        self.assertEqual(RawEvent.objects.count(), initial_event_count + 1)
        latest_event = RawEvent.objects.latest('id')
        self.assertEqual(latest_event.event_name, 'deal.won')

    def test_reprocessing_raw_event_does_not_create_duplicate_deal_events(self):
        from cdp_core.models import RawEvent
        from cdp_core.tasks import process_event_task
        
        raw_event = RawEvent.objects.create(
            company=self.company,
            customer=self.customer,
            event_name='order.completed',
            raw_payload={"email": "idem@test.com", "amount": 500},
            processed=False
        )
        
        process_event_task(raw_event.id)
        
        # Second time
        process_event_task(raw_event.id)
        
        # Deal count should be 1 (only created on first process because we check processed=True)
        # Actually wait, order.completed creates a Deal if it hasn't, but wait, process_event_task creates it every time unless we skip!
        # Because we added `if raw_event.processed: return True`, it won't run again.
        
        deals = Deal.objects.filter(customer=self.customer)
        self.assertEqual(deals.count(), 1)
        
        # There should be exactly 2 events: the order.completed and the deal.won
        self.assertEqual(RawEvent.objects.filter(customer=self.customer).count(), 2)



