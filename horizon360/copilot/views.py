from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import CopilotService, DeterministicProvider
from .intents import IntentResolver
from .context import ContextBuilder
from cdp_core.models import Company, UserProfile
import logging

logger = logging.getLogger(__name__)

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

class CopilotChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required"}, status=400)
            
        company = get_or_create_user_company(request.user)
        service = CopilotService()
        
        try:
            response_data = service.handle(company, query)
            return Response(response_data)
        except Exception as e:
            logger.exception(f"Error handling copilot query: {e}")
            intent = IntentResolver.resolve(query)
            context = ContextBuilder.build_context(company, intent)
            fallback_resp = DeterministicProvider().generate(query, context, company)
            return Response(fallback_resp)
