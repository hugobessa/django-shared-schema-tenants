from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from model_utils.models import TimeStampedModel
from model_utils.choices import Choices
from model_utils.fields import StatusField

from shared_schema_tenants.mixins import SingleTenantModelMixin, MultipleTenantsModelMixin


class TenantSpecificTable(SingleTenantModelMixin):
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = [('tenant', 'name')]

    def __str__(self):
        return '%s/%s' % (self.tenant.slug, self.name)


class TenantSpecificFieldsValidator(MultipleTenantsModelMixin):
    module_path = models.CharField(max_length=255)
    tenants = models.ManyToManyField('Tenant', related_name='validators_available')

    def __str__(self):
        return self.module_path


class TenantSpecificFieldDefinition(SingleTenantModelMixin):
    name = models.CharField(max_length=255)
    DATA_TYPES = Choices('char', 'text', 'integer', 'float', 'datetime', 'date')
    data_type = StatusField(choices_name=DATA_TYPES)
    is_required = models.BooleanField(default=False)
    default_value = models.TextField()
    validators = models.ManyToManyField('TenantSpecificFieldsValidator')
    content_type = models.ForeignKey(ContentType)

    # This only must be filled if the content_type is TenantSpecificTable
    table = models.ForeignKey('TenantSpecificTable', related_name='fields_definitions',
                              blank=True, null=True)

    class Meta:
        unique_together = [('tenant', 'content_type', 'name')]

    def __str__(self):
        content_type = '%s/%s' % (self.tenant.slug, str(self.content_type))
        if content_type == 'shared_schema_tenants.TenantSpecificTable':
            content_type = str(self.table)

        return '%s/%s' % (content_type, self.name)


class TenantSpecificTableRow(TimeStampedModel, SingleTenantModelMixin, ):
    table = models.ForeignKey('TenantSpecificTable', related_name='rows')

    def __str__(self):
        return ', '.join(str(value) for value in self.chunks.all())


class TenantSpecificFieldChunk(models.Model):
    value_integer = models.IntegerField(blank=True, null=True)
    value_char = models.CharField(max_length=255, blank=True, null=True)
    value_text = models.TextField(blank=True, null=True)
    value_float = models.FloatField(blank=True, null=True)
    value_datetime = models.DateTimeField(blank=True, null=True)
    value_date = models.DateField(blank=True, null=True)

    definition = models.ForeignKey('TenantSpecificFieldDefinition', related_name='chunks')

    row_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    row_id = models.PositiveIntegerField()
    row = GenericForeignKey('row_content_type', 'row_id', related_query_name='chunks')

    class Meta:
        unique_together = [('definition', 'row')]

    def __str__(self):
        return '%s: %s' % (
            str(self.definition), str(getattr(self, 'value_' + self.definition.data_type))
        )
