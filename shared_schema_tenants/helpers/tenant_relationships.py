from django.db import transaction
from shared_schema_tenants.models import TenantRelationship


def create_relationship(tenant, user, groups=[], permissions=[]):
    with transaction.atomic():
        relationship = TenantRelationship.objects.create(user=user, tenant=tenant)
        try:
            relationship.groups.set(groups)
            relationship.permissions.set(permissions)
        except AttributeError:
            # compatibility with old django 1.8 and 1.9
            for group in groups:
                relationship.groups.add(group)
            for perm in permissions:
                relationship.permissions.add(perm)

        return relationship
