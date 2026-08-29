from django.urls import path
from .views import CopilotChatView

urlpatterns = [
    path('chat/', CopilotChatView.as_view(), name='copilot-chat'),
]
