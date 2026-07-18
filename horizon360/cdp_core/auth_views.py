from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Company, UserProfile
from rest_framework.permissions import AllowAny

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        company_name = request.data.get('company_name')

        if not email or not password or not company_name:
            return Response({"error": "email, password, and company_name are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=email).exists():
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Multi-tenant provisioning
        company = Company.objects.create(name=company_name)
        user = User.objects.create_user(username=email, email=email, password=password)
        UserProfile.objects.create(user=user, company=company)

        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "Registration successful",
            "company_api_token": str(company.api_token),
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            company_api_token = None
            if hasattr(user, 'profile'):
                company_api_token = str(user.profile.company.api_token)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "company_api_token": company_api_token
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Client handles discarding the access token. 
        # We can accept the refresh token here to blacklist it if configured.
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
