from django.contrib.auth.models import Group, Permission
from django.db import transaction


def create_relationship(tenant, user, groups=[], permissions=[]):
    with transaction.atomic:
        relationship = TenantRelationship.objects.create(user=user, tenant=tenant)
        relationship.set(groups=groups)
        relationship.set(permissions=permissions)
        return relationship