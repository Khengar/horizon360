import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horizon360.settings')
django.setup()

from django.contrib.auth.models import User
from cdp_core.models import Company, UserProfile

def setup():
    # 1. Create Superuser (God Mode)
    if not User.objects.filter(username='root').exists():
        User.objects.create_superuser('root', 'root@example.com', 'root')
        print("Created superuser: root / root")

    # 2. Create Company & Admin (Tenant Mode)
    company, _ = Company.objects.get_or_create(name='Default Corp')
    
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        admin_user = User.objects.create_user(username='admin', email='admin@example.com', password='admin')
        print("Created company admin: admin / admin")
    else:
        admin_user.set_password('admin')
        admin_user.save()
        print("Reset company admin password to: admin")
        
    UserProfile.objects.get_or_create(user=admin_user, defaults={'company': company})
    print("Startup setup complete!")

if __name__ == '__main__':
    setup()
