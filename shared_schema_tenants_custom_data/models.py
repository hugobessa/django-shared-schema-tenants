from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed

from model_utils.models import TimeStampedModel
from model_utils.choices import Choices
from model_utils.fields import StatusField

from shared_schema_tenants.mixins import SingleTenantModelMixin, MultipleTenantsModelMixin
from shared_schema_tenants.models import TenantRelationship
from shared_schema_tenants_custom_data.mixins import TenantSpecificFieldsModelMixin, TenantSpecificPivotTable
from shared_schema_tenants_custom_data.managers import TenantSpecificTableRowManager


class TenantSpecificTable(SingleTenantModelMixin):
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = [('tenant', 'name')]

    def __str__(self):
        return '%s/%s' % (self.tenant.slug, self.name)

    @property
    def fields_definitions(self):
        return TenantSpecificFieldDefinition.objects.filter(
            table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
            table_id=self.id)

    def save(self, *args, **kwargs):
        super(TenantSpecificTable, self).save(*args, **kwargs)
        tstgroup = TenantSpecificTablesGroup.objects.get(group__name='tenant_owner')
        tstgroup.permissions.add(TenantSpecificTablesPermission.objects.create(
            name="add", table=self, codename="add_" + self.name))
        tstgroup.permissions.add(TenantSpecificTablesPermission.objects.create(
            name="change", table=self, codename="change_" + self.name))
        tstgroup.permissions.add(TenantSpecificTablesPermission.objects.create(
            name="delete", table=self, codename="delete_" + self.name))


class TenantSpecificTablesPermission(SingleTenantModelMixin):
    name = models.CharField(max_length=255)
    table = models.ForeignKey('TenantSpecificTable')
    codename = models.CharField(max_length=100)


class TenantSpecificTablesGroup(SingleTenantModelMixin):
    group = models.ForeignKey(
        Group, related_name='tenant_specific_tables_groups')
    permissions = models.ManyToManyField(
        'TenantSpecificTablesPermission', blank=True, related_name='groups')

    class Meta:
        unique_together = (['group', 'tenant'])


@receiver(post_save, sender=Group)
def create_tenant_specific_tables_group(sender, instance, created, *args, **kwargs):
    if created:
        new_group = TenantSpecificTablesGroup.objects.create(
            group=instance)
        if instance.name == 'tenant_owner':
            for perm in TenantSpecificTablesPermission.objects.all():
                new_group.permissions.add(perm)


class TenantSpecificTablesRelationship(SingleTenantModelMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    groups = models.ManyToManyField(
        'TenantSpecificTablesGroup', related_name='relationships')
    permissions = models.ManyToManyField(
        'TenantSpecificTablesPermission', related_name='relationships')


@receiver(post_save, sender=TenantRelationship)
def create_tenant_specific_tables_relationship(sender, instance, created, *args, **kwargs):
    if created:
        new_rel = TenantSpecificTablesRelationship.objects.create(
            user=instance.user, tenant=instance.tenant)
        for group in instance.groups.all():
            tstgroup = TenantSpecificTablesGroup.objects.get(group=group)
            new_rel.groups.add(tstgroup)


@receiver(m2m_changed, sender=TenantRelationship.groups.through)
def add_group_tenant_specific_tables_relationship(sender, instance, action, *args, **kwargs):
    if action == 'post_add':
        rel, created = TenantSpecificTablesRelationship.objects.get_or_create(
            user=instance.user, tenant=instance.tenant)
        for group in instance.groups.all():
            tstgroup = TenantSpecificTablesGroup.objects.get(group=group)
            rel.groups.add(tstgroup)


class TenantSpecificFieldsValidator(MultipleTenantsModelMixin):
    module_path = models.CharField(max_length=255)
    tenants = models.ManyToManyField('shared_schema_tenants.Tenant', related_name='validators_available')

    def __str__(self):
        return self.module_path


class TenantSpecificFieldDefinition(SingleTenantModelMixin):
    name = models.CharField(max_length=255)
    DATA_TYPES = Choices('char', 'text', 'integer', 'float', 'datetime', 'date')
    data_type = StatusField(choices_name='DATA_TYPES')
    is_required = models.BooleanField(default=False)
    default_value = models.TextField()
    validators = models.ManyToManyField('TenantSpecificFieldsValidator', blank=True)

    table_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    table_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = [('tenant', 'table_id', 'table_content_type', 'name')]

    def __str__(self):
        content_type = '%s/%s' % (self.tenant.slug, str(self.table_content_type))
        if content_type == 'shared_schema_tenants.TenantSpecificTable':
            content_type = str(self.table)

        return '%s.%s' % (content_type, self.name)


class TenantSpecificFieldIntegerPivot(SingleTenantModelMixin, TenantSpecificPivotTable):
    value = models.IntegerField()

    def __str__(self):
        return '%s: %d' % (str(self.definition), self.value)


class TenantSpecificFieldCharPivot(SingleTenantModelMixin, TenantSpecificPivotTable):
    value = models.CharField(max_length=255)


class TenantSpecificFieldTextPivot(SingleTenantModelMixin, TenantSpecificPivotTable):
    value = models.TextField()


class TenantSpecificFieldFloatPivot(SingleTenantModelMixin, TenantSpecificPivotTable):
    value = models.FloatField()

    def __str__(self):
        return '%s: %f' % (str(self.definition), self.value)


class TenantSpecificFieldDatePivot(SingleTenantModelMixin, TenantSpecificPivotTable):
    value = models.DateField()

    def __str__(self):
        return '%s: %s' % (str(self.definition), self.value.isoformat())


class TenantSpecificFieldDateTimePivot(SingleTenantModelMixin, TenantSpecificPivotTable):
    value = models.DateTimeField()

    def __str__(self):
        return '%s: %s' % (str(self.definition), self.value.isoformat())


class TenantSpecificTableRow(TimeStampedModel, SingleTenantModelMixin, TenantSpecificFieldsModelMixin):
    table = models.ForeignKey('TenantSpecificTable', related_name='rows')

    objects = TenantSpecificTableRowManager()

    original_manager = models.Manager()
    tenant_objects = TenantSpecificTableRowManager()

    class Meta:
        default_manager_name = 'original_manager'
        base_manager_name = 'original_manager'

    def __str__(self):
        return ', '.join(str(p) for p in self.pivots)

    @property
    def fields_definitions(self):
        return self.table.fields_definitions

    @property
    def values_dict(self):
        from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
            _get_pivot_table_class_for_data_type)
        definitions = self.table.fields_definitions
        row_content_type = ContentType.objects.get_for_model(self.__class__)
        values = {
            d.name: _get_pivot_table_class_for_data_type(d.data_type).objects.get(
                row_id=self.id, row_content_type=row_content_type).value
            for d in definitions
        }

        return values

    @property
    def pivots(self):
        from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
            _get_pivot_table_class_for_data_type)
        definitions = self.table.fields_definitions
        row_content_type = ContentType.objects.get_for_model(self.__class__)
        values_list = {
            d.name: _get_pivot_table_class_for_data_type(d.data_type).objects.get(
                row_id=self.id, row_content_type=row_content_type)
            for d in definitions
        }

        return values_list

    def update_tenant_specific_fields(self, tenant_specific_fields_data):
        from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
            get_custom_table_manager, _get_pivot_table_class_for_data_type)

        old = get_custom_table_manager(self.table.name).get(pk=self.pk)
        definitions = self.get_definitions()
        definitions_by_name = {d.name: d for d in definitions}

        with transaction.atomic():
            for field_name, definition in definitions_by_name.items():
                new_value = tenant_specific_fields_data.get(
                    field_name, None)
                old_value = getattr(old, field_name, None)
                if new_value != old_value:
                    PivotTableClass = _get_pivot_table_class_for_data_type(definition.data_type)
                    PivotTableClass.objects.filter(
                        definition__id=definition.id, row_id=self.id,
                        row_content_type=ContentType.objects.get_for_model(self.__class__)
                    ).update(value=new_value)
