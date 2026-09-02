import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horizon360.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = 'admin@shopez.com'
password = 'ShopEZ_SecurePassword2026!'

# If the custom user model requires email as the USERNAME_FIELD
if not User.objects.filter(email=email).exists():
    if User.USERNAME_FIELD == 'email':
        User.objects.create_superuser(email=email, password=password)
    else:
        User.objects.create_superuser(username=email, email=email, password=password)
    print(f"✅ User {email} created successfully!")
else:
    print(f"ℹ️ User {email} already exists.")
