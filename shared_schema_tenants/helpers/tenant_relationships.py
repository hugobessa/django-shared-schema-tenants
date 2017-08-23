from django.db import transaction
from shared_schema_tenants.models import TenantRelationship


def create_relationship(tenant, user, groups=[], permissions=[]):
    with transaction.atomic():
        relationship = TenantRelationship.objects.create(user=user, tenant=tenant)
        relationship.groups.set(groups)
        relationship.permissions.set(permissions)
        return relationship
