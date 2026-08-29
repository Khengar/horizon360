from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import CopilotService

class CopilotChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required"}, status=400)
            
        if not hasattr(request.user, 'profile') or not request.user.profile.company:
            return Response({"error": "User does not have an associated company"}, status=403)
            
        company = request.user.profile.company
        service = CopilotService()
        
        response_data = service.handle(company, query)
        return Response(response_data)
