from rest_framework import viewsets
from .models import Contact, Deal
from .serializers import ContactSerializer, DealSerializer
from cdp_core.models import Company, UserProfile

def get_or_create_user_company(user):
    if hasattr(user, 'profile') and user.profile and user.profile.company:
        return user.profile.company
    company = Company.objects.first()
    if not company:
        company = Company.objects.create(name='Default Corp')
    if user and user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'company': company})
        if not profile.company:
            profile.company = company
            profile.save()
    return company

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contact.objects.none()
        company = get_or_create_user_company(self.request.user)
        return Contact.objects.filter(company=company)

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)

class DealViewSet(viewsets.ModelViewSet):
    serializer_class = DealSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Deal.objects.none()
        company = get_or_create_user_company(self.request.user)
        return Deal.objects.filter(company=company)

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
