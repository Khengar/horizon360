import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cdp_core.models import EventSchema, RawEvent, Customer
from crm.models import Contact, Deal
from cdp_core.tasks import process_event_task

class Command(BaseCommand):
    help = 'Seeds the database with schemas, customer journeys, and CRM data.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Registering schemas...')
        EventSchema.objects.get_or_create(
            event_name='user.identified',
            defaults={'json_schema': {"type": "object", "properties": {"email": {"type": "string"}}}}
        )
        EventSchema.objects.get_or_create(
            event_name='page.viewed',
            defaults={'json_schema': {"type": "object", "properties": {"url": {"type": "string"}}}}
        )
        EventSchema.objects.get_or_create(
            event_name='order.completed',
            defaults={'json_schema': {"type": "object", "properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}}}}
        )

        self.stdout.write('Generating customer journeys for 5 users...')
        users = [
            {"email": "alice@example.com", "phone": "111-1111", "name": "Alice Smith"},
            {"email": "bob@example.com", "phone": "222-2222", "name": "Bob Jones"},
            {"email": "charlie@example.com", "phone": "333-3333", "name": "Charlie Brown"},
            {"email": "diana@example.com", "phone": "444-4444", "name": "Diana Prince"},
            {"email": "evan@example.com", "phone": "555-5555", "name": "Evan Wright"},
        ]

        for u in users:
            # Event 1: Identify the user (with consent flags)
            r1 = RawEvent.objects.create(
                event_name='user.identified',
                raw_payload={
                    "email": u["email"], 
                    "phone": u["phone"], 
                    "traits": {"name": u["name"]},
                    "consent": {"marketing": True, "data_sale": False}
                }
            )
            # Process synchronously for the seed script to guarantee CRM creation can lookup Customers immediately
            process_event_task(r1.id)

            # Event 2: Page View
            r2 = RawEvent.objects.create(
                event_name='page.viewed',
                raw_payload={"email": u["email"], "url": "/pricing"}
            )
            process_event_task(r2.id)

            # Event 3: Order (Randomized)
            if random.choice([True, False]):
                r3 = RawEvent.objects.create(
                    event_name='order.completed',
                    raw_payload={
                        "email": u["email"], 
                        "order_id": f"ORD-{random.randint(1000,9999)}", 
                        "amount": round(random.uniform(50, 300), 2),
                        "cart_value": 150 # Setting attribute to hit dynamic segment 'high-value-cart' optionally
                    }
                )
                process_event_task(r3.id)

        self.stdout.write('Creating CRM data for 2 customers...')
        # Extract 2 known customers
        target_customers = Customer.objects.filter(primary_email__in=["alice@example.com", "bob@example.com"])
        admin_user, _ = User.objects.get_or_create(username='admin', email='admin@example.com')
        
        for idx, customer in enumerate(target_customers):
            contact, created = Contact.objects.get_or_create(customer=customer, defaults={'owner': admin_user})
            if created:
                Deal.objects.create(
                    contact=contact,
                    stage='qualified' if idx == 0 else 'won',
                    value=5000.00 if idx == 0 else 12500.50
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
