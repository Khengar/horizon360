from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from cdp_core.models import Company, UserProfile, Customer, RawEvent
from finance.models import Invoice, Payment, JournalEntry

class Phase4FinanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.company = Company.objects.create(name="Apex Global Corp", plan="enterprise")
        self.user = User.objects.create_user(username="fin_admin", password="password123", email="fin@apex.com")
        self.profile = UserProfile.objects.create(user=self.user, company=self.company)

        self.customer = Customer.objects.create(
            company=self.company,
            primary_email="billing@client.com"
        )
        self.client.force_authenticate(user=self.user)

    def test_invoice_creation_and_balance_due(self):
        res = self.client.post('/api/v1/finance/invoices/', {
            "customer": str(self.customer.id),
            "invoice_number": "INV-2026-001",
            "amount": "10000.00",
            "currency": "USD",
            "status": "issued"
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        invoice_id = res.data['id']

        invoice = Invoice.objects.get(id=invoice_id)
        self.assertEqual(invoice.amount, Decimal('10000.00'))
        self.assertEqual(invoice.amount_paid, Decimal('0.00'))
        self.assertEqual(invoice.balance_due, Decimal('10000.00'))

        # Verify initial invoice journal entries (AR debit, Revenue credit)
        ar_entry = JournalEntry.objects.filter(company=self.company, account_code='1200_ACCOUNTS_RECEIVABLE', reference_id=str(invoice.id)).first()
        self.assertIsNotNone(ar_entry)
        self.assertEqual(ar_entry.entry_type, 'debit')

    def test_payment_recording_and_automated_reconciliation(self):
        invoice = Invoice.objects.create(
            company=self.company,
            customer=self.customer,
            invoice_number="INV-2026-002",
            amount=Decimal('5000.00'),
            status="issued"
        )

        # 1. Partial Payment ($2000)
        pay1_res = self.client.post(f'/api/v1/finance/invoices/{invoice.id}/record-payment/', {
            "amount": "2000.00",
            "payment_method": "credit_card",
            "transaction_id": "txn_partial_123"
        }, format='json')
        self.assertEqual(pay1_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(pay1_res.data['invoice_status'], 'partially_paid')
        self.assertEqual(pay1_res.data['amount_paid'], 2000.00)
        self.assertEqual(pay1_res.data['balance_due'], 3000.00)

        # 2. Final Payment ($3000)
        pay2_res = self.client.post(f'/api/v1/finance/invoices/{invoice.id}/record-payment/', {
            "amount": "3000.00",
            "payment_method": "bank_transfer",
            "transaction_id": "txn_final_456"
        }, format='json')
        self.assertEqual(pay2_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(pay2_res.data['invoice_status'], 'paid')
        self.assertEqual(pay2_res.data['amount_paid'], 5000.00)
        self.assertEqual(pay2_res.data['balance_due'], 0.00)

        # 3. Verify General Ledger Double-Entry Records
        cash_entries = JournalEntry.objects.filter(company=self.company, account_code='1010_CASH')
        self.assertEqual(cash_entries.count(), 2)

        # 4. Verify CDP Event Emission
        events = RawEvent.objects.filter(company=self.company, customer=self.customer, event_name='payment.completed')
        self.assertEqual(events.count(), 2)
