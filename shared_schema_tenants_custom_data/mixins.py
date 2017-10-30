from django.db import models
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from shared_schema_tenants_custom_data.managers import TenantSpecificFieldsModelManager


class TenantSpecificFieldsModelMixin(models.Model):
    objects = TenantSpecificFieldsModelManager

    def create_tenant_specific_fields(self):
        from shared_schema_tenants_custom_data.models import (
            TenantSpecificFieldDefinition, TenantSpecificFieldChunk)

        definitions = TenantSpecificFieldDefinition.objects.filter(
            content_type=ContentType.objects.get_for_model(self.model))
        definitions_by_name = {d.name: d for d in definitions}

        with transaction.atomic():
            for field_name, definition in definitions_by_name.items():
                field_value = getattr(self, field_name, None)
                TenantSpecificFieldChunk.objects.create(
                    definition_id=definition.id, row=self,
                    **{('value_' + definition.data_type): field_value})

    def update_tenant_specific_fields(self):
        from shared_schema_tenants_custom_data.models import (
            TenantSpecificFieldDefinition, TenantSpecificFieldChunk)

        old = self.__class__.objects.get(self.pk)
        definitions = TenantSpecificFieldDefinition.objects.filter(
            table__content_type=ContentType.objects.get_for_model(self.model))
        definitions_by_name = {d.name: d for d in definitions}

        with transaction.atomic():
            for field_name, definition in definitions_by_name.items():
                new_value = getattr(self, field_name, None)
                old_value = getattr(old, field_name, None)
                if new_value != old_value:
                    TenantSpecificFieldChunk.objects.filter(
                        definition_id=definition.id, row=self).update(
                        **{('value_' + definition.data_type): new_value})

    def save(self, *args, **kwargs):
        if not self.pk:
            super(TenantSpecificFieldsModelMixin, self).save(*args, **kwargs)
            self.create_tenant_specific_fields()
        else:
            super(TenantSpecificFieldsModelMixin, self).save(*args, **kwargs)
            self.update_tenant_specific_fields()

    @classmethod
    def fields_definitions(cls):
        from shared_schema_tenants_custom_data.models import TenantSpecificFieldDefinition
        return TenantSpecificFieldDefinition.objects.filter(
            table_content_type=ContentType.objects.get_for_model(cls))

    class Meta:
        abstract = True
