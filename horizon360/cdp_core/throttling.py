from rest_framework.throttling import UserRateThrottle

class TenantRateThrottle(UserRateThrottle):
    """
    Dynamically adjusts API request rate quotas based on the tenant's subscription plan.
    - Starter: 100/minute
    - Professional: 500/minute
    - Enterprise: 2000/minute
    """
    scope = 'tenant'

    PLAN_RATES = {
        'starter': '100/min',
        'professional': '500/min',
        'enterprise': '2000/min',
    }

    def get_rate(self):
        request = getattr(self, 'request', None)
        if request and request.user and request.user.is_authenticated:
            if hasattr(request.user, 'profile') and request.user.profile.company:
                plan = request.user.profile.company.plan or 'starter'
                return self.PLAN_RATES.get(plan.lower(), '100/min')
        return '60/min'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            if hasattr(request.user, 'profile') and request.user.profile.company:
                ident = f"tenant_{request.user.profile.company.id}_{request.user.id}"
            else:
                ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
