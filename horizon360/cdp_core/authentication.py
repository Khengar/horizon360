from rest_framework import authentication
from rest_framework import exceptions
from .models import Company

class APITokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return None

        try:
            company = Company.objects.get(api_token=api_key, is_active=True)
        except Company.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or inactive API Key')

        user = company.users.first().user if company.users.exists() else None
        
        if not user:
             raise exceptions.AuthenticationFailed('No user associated with this company')
             
        return (user, None)
