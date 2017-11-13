from django.db import models
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from shared_schema_tenants.helpers.tenants import get_current_tenant
from shared_schema_tenants_custom_data.managers import TenantSpecificFieldsModelManager


class TenantSpecificFieldsModelMixin(models.Model):
    objects = TenantSpecificFieldsModelManager()

    def __init__(self, *args, **kwargs):
        table_id = kwargs.get('table_id', getattr(kwargs.get('table'), 'id', None))
        definitions = self.get_definitions(table_id=table_id)
        self.tenant_specific_fields_data = {}
        for definition in definitions:
            if definition.name in kwargs.keys():
                self.tenant_specific_fields_data[definition.name] = kwargs.pop(definition.name)
        super(TenantSpecificFieldsModelMixin, self).__init__(*args, **kwargs)

    def get_definitions(self, table_id=-1, force_hit_db=False):
        from shared_schema_tenants_custom_data.models import TenantSpecificFieldDefinition, TenantSpecificTable
        if not hasattr(self, 'definitions') or force_hit_db:
            if type(self).__name__ == 'TenantSpecificTableRow':
                self.definitions = TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                    table_id=table_id)
            else:
                self.definitions = TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=ContentType.objects.get_for_model(type(self)))
        return self.definitions

    def create_tenant_specific_fields(self):
        from shared_schema_tenants_custom_data.models import TenantSpecificFieldChunk

        definitions = self.get_definitions()
        definitions_by_name = {d.name: d for d in definitions}

        with transaction.atomic():
            for field_name, definition in definitions_by_name.items():
                field_value = self.tenant_specific_fields_data.get(
                    field_name, getattr(self, field_name, None))
                TenantSpecificFieldChunk.objects.create(
                    definition_id=definition.id, row=self,
                    **{('value_' + definition.data_type): field_value})

    def update_tenant_specific_fields(self):
        from shared_schema_tenants_custom_data.models import TenantSpecificFieldChunk

        old = self.__class__.objects.get(pk=self.pk)
        definitions = self.get_definitions()
        definitions_by_name = {d.name: d for d in definitions}

        with transaction.atomic():
            for field_name, definition in definitions_by_name.items():
                new_value = self.tenant_specific_fields_data.get(field_name, None)
                old_value = getattr(old, field_name, None)
                if new_value != old_value:
                    TenantSpecificFieldChunk.objects.filter(
                        definition_id=definition.id, row=self).update(
                        **{('value_' + definition.data_type): new_value})

    def save(self, *args, **kwargs):
        table_id = getattr(self, 'table_id', getattr(getattr(self, 'table', object()), 'id', None))

        force_hit_db = False
        if hasattr(self, 'definitions') and not self.definitions.exists():
            force_hit_db = True

        definitions = self.get_definitions(table_id=table_id, force_hit_db=force_hit_db)
        for definition in definitions:
            if definition.name not in self.tenant_specific_fields_data.keys():
                if hasattr(self, definition.name):
                    self.tenant_specific_fields_data[definition.name] = getattr(self, definition.name)
                    delattr(self, definition.name)
                else:
                    self.tenant_specific_fields_data[definition.name] = definition.default_value

        if not self.pk:
            if not hasattr(self, 'tenant'):
                self.tenant = get_current_tenant()
            super(TenantSpecificFieldsModelMixin, self).save(*args, **kwargs)
            self.create_tenant_specific_fields()
        else:
            super(TenantSpecificFieldsModelMixin, self).save(*args, **kwargs)
            self.update_tenant_specific_fields()

    @property
    def fields_definitions(self):
        return self.get_definitions()

    class Meta:
        abstract = True
