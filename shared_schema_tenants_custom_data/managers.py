from django.db import models
from django.utils.version import get_complete_version

from django.contrib.contenttypes.models import ContentType

from shared_schema_tenants_custom_data.querysets import TenantSpecificFieldsQueryset
from shared_schema_tenants.managers import SingleTenantModelManager


class TenantSpecificFieldsModelManager(models.Manager):
    queryset = TenantSpecificFieldsQueryset
    data_type_fields = {
        'integer': models.IntegerField(),
        'char': models.CharField(max_length=255),
        'text': models.TextField(),
        'float': models.FloatField(),
        'datetime': models.DateTimeField(),
        'date': models.DateField(),
    }

    def get_queryset(self, *args, **kwargs):
        custom_fields_annotations = self._get_custom_fields_annotations()

        if len(custom_fields_annotations.keys()) > 0:
            return super().annotate(**custom_fields_annotations).get_queryset(*args, **kwargs)

        return super().get_queryset(*args, **kwargs)

    def _get_custom_fields_annotations(self):
        from shared_schema_tenants_custom_data.models import (
            TenantSpecificFieldDefinition, TenantSpecificFieldChunk)

        definitions = TenantSpecificFieldDefinition.objects.filter(
            table__content_type=ContentType.objects.get_for_model(self.model))
        definitions_by_name = {d.name: d for d in definitions}

        custom_fields_annotations = {}

        for key in definitions_by_name.keys():
            if get_complete_version()[1] >= 11:
                from django.db.models import Subquery, OuterRef
                definitions_values = (
                    TenantSpecificFieldChunk.objects
                    .filter(definition_id=definitions_by_name[key].id, row_id=OuterRef('pk'))
                    .aggregate(value=models.F('value_' + definitions_by_name[key].data_type))
                    .values('value')
                )
                definitions_values.query.group_by = []

                custom_fields_annotations[key] = Subquery(
                    queryset=definitions_values,
                    output_field=self.data_type_fields[definitions_by_name[key].data_type]
                )
            else:
                from django.db.models.expressions import RawSQL
                custom_fields_annotations[key] = RawSQL("""
                        select c.value_%(data_type)s
                        from shared_schema_tenants_custom_data_tenantspecificfieldchunk c
                        where definition_id = %(definition_id)s and c.row_id = %(row_id)s
                    """, params={
                    'data_type': definitions_by_name[key].data_type,
                    'definition_id': definitions_by_name[key].id,
                    'row_id': models.F('pk')
                }, output_field=self.data_type_fields[definitions_by_name[key].data_type])

        return custom_fields_annotations


class TenantSpecificTableRowManager(SingleTenantModelManager, TenantSpecificFieldsModelManager):
    pass
