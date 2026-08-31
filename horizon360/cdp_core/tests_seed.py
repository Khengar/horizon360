from django.test import TestCase
from django.core.management import call_command
from cdp_core.models import Company, Customer
from marketing.models import Campaign, Lead
from crm.models import Deal
from finance.models import Invoice

class SeedDemoTests(TestCase):
    def test_seed_command_idempotency(self):
        # Initial state
        self.assertEqual(Company.objects.count(), 0)
        
        # Run command once
        call_command('seed_horizon_demo')
        
        # Verify initial data created
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Customer.objects.count(), 2)
        self.assertEqual(Deal.objects.count(), 1)
        self.assertEqual(Invoice.objects.count(), 1)
        
        # Run command a second time
        call_command('seed_horizon_demo')
        
        # Verify no duplicates created
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Customer.objects.count(), 2)
        self.assertEqual(Deal.objects.count(), 1)
        self.assertEqual(Invoice.objects.count(), 1)
