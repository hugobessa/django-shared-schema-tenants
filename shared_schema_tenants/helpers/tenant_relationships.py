from django.db import transaction
from shared_schema_tenants.models import TenantRelationship


def create_relationship(tenant, user, groups=[], permissions=[]):
    with transaction.atomic():
        relationship = TenantRelationship.objects.create(user=user, tenant=tenant)
        for group in groups:
            relationship.groups.add(group)
        for perm in permissions:
            relationship.permissions.add(perm)

        return relationship
