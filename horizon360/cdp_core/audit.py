import logging
import json
from typing import Optional, Dict, Any
from django.core.serializers.json import DjangoJSONEncoder
from .models import AuditLog, Company

logger = logging.getLogger(__name__)

def sanitize_json(data: Any) -> Any:
    """
    Ensures that UUIDs, dates, decimals, etc. are safely serialized to JSON-safe primitives.
    """
    if data is None:
        return {}
    try:
        return json.loads(json.dumps(data, cls=DjangoJSONEncoder))
    except Exception:
        return str(data)

def record_audit_log(
    company: Company,
    action: str,
    entity_type: str,
    entity_id: str,
    user: Optional[Any] = None,
    diff: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> Optional[AuditLog]:
    """
    Records an immutable audit log entry for a mutating action on an entity.
    """
    try:
        if not company:
            return None
            
        actual_user = user if user and getattr(user, 'is_authenticated', False) else None
        safe_diff = sanitize_json(diff or {})

        log = AuditLog.objects.create(
            company=company,
            user=actual_user,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            diff=safe_diff,
            ip_address=ip_address
        )
        return log
    except Exception as e:
        logger.exception(f"Failed to record audit log: {e}")
        return None


def get_client_ip(request) -> Optional[str]:
    """
    Extracts the client IP from request headers.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class AuditLoggingMixin:
    """
    ViewSet mixin that automatically captures create, update, and delete actions in AuditLog.
    """
    def perform_create(self, serializer):
        instance = serializer.save()
        user = getattr(self.request, 'user', None)
        company = getattr(instance, 'company', None)
        if not company and hasattr(self, 'get_company'):
            company = self.get_company()
        elif not company and user and hasattr(user, 'profile'):
            company = user.profile.company

        if company:
            record_audit_log(
                company=company,
                action='create',
                entity_type=instance.__class__.__name__,
                entity_id=str(instance.pk),
                user=user,
                diff={'created': sanitize_json(serializer.data)},
                ip_address=get_client_ip(self.request)
            )

    def perform_update(self, serializer):
        instance = self.get_object()
        old_data = {}
        if hasattr(serializer.__class__, 'Meta') and hasattr(serializer.__class__.Meta, 'model'):
            try:
                old_data = {
                    field: getattr(instance, field, None)
                    for field in serializer.validated_data.keys()
                    if hasattr(instance, field) and not callable(getattr(instance, field))
                }
            except Exception:
                pass

        instance = serializer.save()
        user = getattr(self.request, 'user', None)
        company = getattr(instance, 'company', None)
        if not company and user and hasattr(user, 'profile'):
            company = user.profile.company

        if company:
            record_audit_log(
                company=company,
                action='update',
                entity_type=instance.__class__.__name__,
                entity_id=str(instance.pk),
                user=user,
                diff={
                    'before': sanitize_json(old_data),
                    'after': sanitize_json(serializer.validated_data)
                },
                ip_address=get_client_ip(self.request)
            )

    def perform_destroy(self, instance):
        entity_type = instance.__class__.__name__
        entity_id = str(instance.pk)
        user = getattr(self.request, 'user', None)
        company = getattr(instance, 'company', None)
        if not company and user and hasattr(user, 'profile'):
            company = user.profile.company

        instance.delete()

        if company:
            record_audit_log(
                company=company,
                action='delete',
                entity_type=entity_type,
                entity_id=entity_id,
                user=user,
                diff={'deleted': True},
                ip_address=get_client_ip(self.request)
            )

