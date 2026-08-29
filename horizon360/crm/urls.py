from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, DealViewSet

router = DefaultRouter()
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'deals', DealViewSet, basename='deal')

urlpatterns = [
    path('', include(router.urls)),
]
