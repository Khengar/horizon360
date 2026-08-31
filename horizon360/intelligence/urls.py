from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InsightViewSet, RunMeshView, ExecuteActionView

router = DefaultRouter()
router.register(r'insights', InsightViewSet, basename='insight')

urlpatterns = [
    path('run/', RunMeshView.as_view(), name='run-mesh'),
    path('action/', ExecuteActionView.as_view(), name='execute-action'),
    path('', include(router.urls)),
]
