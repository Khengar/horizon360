"""
URL configuration for horizon360 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

v1_patterns = [
    path('cdp/', include('cdp_core.urls')),
    path('crm/', include('crm.urls')),
    path('finance/', include('finance.urls')),
    path('service/', include('service.urls')),
    path('marketing/', include('marketing.urls')),
    path('projects/', include('projects.urls')),
    path('hrms/', include('hrms.urls')),
    path('partner/', include('partner.urls')),
    path('vendor/', include('vendor.urls')),
    path('integrations/', include('integrations.urls')),
    path('nexus/', include('integrations.urls')),
    path('intelligence/', include('intelligence.urls')),
    path('copilot/', include('copilot.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    # Version 1 Standard Endpoints
    path('api/v1/', include(v1_patterns)),
    # Default API Endpoints
    path('api/', include('cdp_core.urls')),
    path('api/crm/', include('crm.urls')),
    path('api/intelligence/', include('intelligence.urls')),
    path('api/copilot/', include('copilot.urls')),
    path('api/finance/', include('finance.urls')),
    path('api/service/', include('service.urls')),
    path('api/marketing/', include('marketing.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/hrms/', include('hrms.urls')),
    path('api/partner/', include('partner.urls')),
    path('api/vendor/', include('vendor.urls')),
    path('api/integrations/', include('integrations.urls')),
    path('api/nexus/', include('integrations.urls')),
]


