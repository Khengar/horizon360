import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horizon360.settings')
django.setup()

from django.contrib.auth.models import User
from cdp_core.models import Company, UserProfile, EventSchema, RawEvent, Customer

print("Previous Data:")
print("Companies:", Company.objects.all())
print("Users:", User.objects.all())
print("Events:", RawEvent.objects.all())

# Create a new company
company, created = Company.objects.get_or_create(name="ShopEZ Inc.")
print(f"Company ShopEZ Inc. {'created' if created else 'already exists'}.")

# Create a new admin for the company
if not User.objects.filter(username="shopez_admin").exists():
    user = User.objects.create_superuser("shopez_admin", "admin@shopez.com", "shopez_password")
    UserProfile.objects.create(user=user, company=company)
    print("User shopez_admin created and linked to ShopEZ Inc.")
else:
    print("User shopez_admin already exists.")
