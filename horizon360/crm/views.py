from rest_framework import viewsets
from .models import Contact, Deal
from .serializers import ContactSerializer, DealSerializer

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer

    def get_queryset(self):
        if not hasattr(self.request.user, 'profile'):
            return Contact.objects.none()
        return Contact.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'profile'):
            serializer.save(company=self.request.user.profile.company)
        else:
            serializer.save()

class DealViewSet(viewsets.ModelViewSet):
    serializer_class = DealSerializer

    def get_queryset(self):
        if not hasattr(self.request.user, 'profile'):
            return Deal.objects.none()
        return Deal.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'profile'):
            serializer.save(company=self.request.user.profile.company)
        else:
            serializer.save()
