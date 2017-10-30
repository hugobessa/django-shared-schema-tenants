from django.db import models
from django.db.models import QuerySet
from django.contrib.contenttypes.models import ContentType


class TenantSpecificFieldsQueryset(QuerySet):
    data_type_fields = {
        'integer': models.IntegerField(),
        'char': models.CharField(max_length=255),
        'text': models.TextField(),
        'float': models.FloatField(),
        'datetime': models.DateTimeField(),
        'date': models.DateField(),
    }

    def update(self, *args, **kwargs):
        from shared_schema_tenants_custom_data.models import (
            TenantSpecificFieldDefinition, TenantSpecificFieldChunk)

        definitions = TenantSpecificFieldDefinition.objects.filter(
            table__content_type=ContentType.objects.get_for_model(self.model))
        definitions_by_name = {d.name: d for d in definitions}

        custom_fields = {k: v for k, v in kwargs.items() if k in definitions_by_name.keys()}
        common_fields = {k: v for k, v in kwargs.items() if k not in definitions_by_name.keys()}

        super().update(**common_fields)

        for field_name, field_value in custom_fields.items():
            (TenantSpecificFieldChunk.objects
             .filter(definitions_id=definitions_by_name[field_name].id)
             .update(**{('value_' + definitions_by_name[field_name].data_type): field_value}))
