from django.db import models
from django.db.models import QuerySet, F
from django.db.models.expressions import RawSQL
from django.utils.version import get_complete_version
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

    def _get_annotate_fields(self):
        from shared_schema_tenants_custom_data.models import (
            TenantSpecificFieldDefinition, TenantSpecificFieldChunk)

        definitions = TenantSpecificFieldDefinition.objects.filter(
            table__content_type=ContentType.objects.get_for_model(self.model))
        definitions_by_name = {d.name: d for d in definitions}

        annotate_fields = {}

        for key in definitions_by_name.keys():
            if get_complete_version()[1] >= 11:
                from django.db.models import Subquery, OuterRef
                definitions_values = (
                    TenantSpecificFieldChunk.objects
                    .filter(definition_id=definitions_by_name[key].id, row_id=OuterRef('pk'))
                    .aggregate(value=F('value_' + definitions_by_name[key].data_type))
                    .values('value')
                )
                definitions_values.query.group_by = []

                annotate_fields[key] = Subquery(
                    queryset=definitions_values,
                    output_field=self.data_type_fields[definitions_by_name[key].data_type]
                )
            else:
                annotate_fields[key] = RawSQL("""
                        select c.value_%(data_type)s
                        from shared_schema_tenants_custom_data_tenantspecificfieldchunk c
                        where definition_id = %(definition_id)s and c.row_id = %(row_id)s
                    """, params={
                    'data_type': definitions_by_name[key].data_type,
                    'definition_id': definitions_by_name[key].id,
                    'row_id': models.F('pk')
                }, output_field=self.data_type_fields[definitions_by_name[key].data_type])

        return annotate_fields

    def get(self, *args, **kwargs):
        annotate_fields = self._get_annotate_fields()

        if len(annotate_fields.keys()) > 0:
            return super().annotate(**annotate_fields).get(*args, **kwargs)

        return super().get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        annotate_fields = self._get_annotate_fields()

        if len(annotate_fields.keys()) > 0:
            return super().annotate(**annotate_fields).filter(*args, **kwargs)

        return super().filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        annotate_fields = self._get_annotate_fields()

        if len(annotate_fields.keys()) > 0:
            return super().annotate(**annotate_fields).exclude(*args, **kwargs)

        return super().exclude(*args, **kwargs)

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
