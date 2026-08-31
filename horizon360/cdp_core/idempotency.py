import json
import logging
from typing import Optional
from django.core.cache import cache
from rest_framework.response import Response

logger = logging.getLogger(__name__)

IDEMPOTENCY_TIMEOUT = 86400  # 24 hours

def get_idempotency_key(request) -> Optional[str]:
    """
    Extracts Idempotency-Key from headers.
    """
    if not request:
        return None
    return (
        request.headers.get('Idempotency-Key') or 
        request.headers.get('X-Idempotency-Key') or 
        request.META.get('HTTP_IDEMPOTENCY_KEY')
    )


class IdempotencyMixin:
    """
    ViewSet mixin that checks for Idempotency-Key header on POST requests.
    If a cached response for the same key exists within 24 hours, returns it directly.
    Otherwise, caches the successful response upon creation.
    """
    def create(self, request, *args, **kwargs):
        idemp_key = get_idempotency_key(request)
        if not idemp_key:
            return super().create(request, *args, **kwargs)

        company_id = getattr(getattr(getattr(request, 'user', None), 'profile', None), 'company_id', 'anon')
        cache_key = f"idemp:{company_id}:{idemp_key}"

        cached_entry = cache.get(cache_key)
        if cached_entry:
            logger.info(f"Returning cached idempotent response for key: {idemp_key}")
            return Response(cached_entry.get('data'), status=cached_entry.get('status', 200))

        response = super().create(request, *args, **kwargs)

        if response.status_code in [200, 201, 202]:
            cache.set(cache_key, {'data': response.data, 'status': response.status_code}, timeout=IDEMPOTENCY_TIMEOUT)

        return response
