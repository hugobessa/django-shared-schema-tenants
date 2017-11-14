import django
from django.db import models, transaction
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from model_utils.models import TimeStampedModel
from model_utils.choices import Choices
from model_utils.fields import StatusField

from shared_schema_tenants.mixins import SingleTenantModelMixin, MultipleTenantsModelMixin
from shared_schema_tenants_custom_data.mixins import TenantSpecificFieldsModelMixin
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


class TenantSpecificFieldChunk(SingleTenantModelMixin):
    value_integer = models.IntegerField(blank=True, null=True)
    value_char = models.CharField(max_length=255, blank=True, null=True)
    value_text = models.TextField(blank=True, null=True)
    value_float = models.FloatField(blank=True, null=True)
    value_datetime = models.DateTimeField(blank=True, null=True)
    value_date = models.DateField(blank=True, null=True)

    definition = models.ForeignKey('TenantSpecificFieldDefinition', related_name='chunks')

    row_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    row_id = models.PositiveIntegerField()
    row = GenericForeignKey(ct_field='row_content_type', fk_field='row_id')

    class Meta:
        unique_together = [('definition', 'row_id', 'row_content_type')]

    def __str__(self):
        return '%s: %s' % (
            str(self.definition), str(getattr(self, 'value_' + self.definition.data_type))
        )


class TenantSpecificTableRow(TimeStampedModel, SingleTenantModelMixin, TenantSpecificFieldsModelMixin):
    table = models.ForeignKey('TenantSpecificTable', related_name='rows')
    chunks = GenericRelation(
        TenantSpecificFieldChunk, object_id_field='row_id', content_type_field='row_content_type')

    if django.utils.version.get_complete_version()[1] < 10:
        objects = models.Manager()
    else:
        objects = TenantSpecificTableRowManager()

    original_manager = models.Manager()
    tenant_objects = TenantSpecificTableRowManager()

    class Meta:
        if django.utils.version.get_complete_version()[1] >= 10:
            default_manager_name = 'original_manager'
            base_manager_name = 'original_manager'

    def __str__(self):
        return ', '.join(str(value) for value in self.chunks.all())

    @property
    def fields_definitions(self):
        return self.table.fields_definitions

    def update_tenant_specific_fields(self, tenant_specific_fields_data):
        from shared_schema_tenants_custom_data.models import TenantSpecificFieldChunk
        from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import get_custom_table_manager

        old = get_custom_table_manager(self.table.name).get(pk=self.pk)
        definitions = self.get_definitions()
        definitions_by_name = {d.name: d for d in definitions}

        with transaction.atomic():
            for field_name, definition in definitions_by_name.items():
                new_value = tenant_specific_fields_data.get(
                    field_name, None)
                old_value = getattr(old, field_name, None)
                if new_value != old_value:
                    TenantSpecificFieldChunk.objects.filter(
                        definition_id=definition.id, row_id=self.id,
                        row_content_type=ContentType.objects.get_for_model(self.__class__)
                    ).update(**{('value_' + definition.data_type): new_value})
