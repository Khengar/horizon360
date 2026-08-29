from rest_framework import viewsets
from .models import Insight
from .serializers import InsightSerializer

class InsightViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InsightSerializer

    def get_queryset(self):
        if not hasattr(self.request.user, 'profile'):
            return Insight.objects.none()
        return Insight.objects.filter(company=self.request.user.profile.company).order_by('-created_at')
