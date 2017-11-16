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

    def __init__(self, *args, **kwargs):
        self.table_id = kwargs.pop('table_id', getattr(kwargs.pop('table', object()), 'id', -1))
        super(TenantSpecificFieldsQueryset, self).__init__(*args, **kwargs)
        self.get_definitions(table_id=self.table_id)

    def _clone(self, **kwargs):
        """
        Return a copy of the current QuerySet. A lightweight alternative
        to deepcopy().
        """
        query = self.query.clone()
        if self._sticky_filter:
            query.filter_is_sticky = True

        clone = self.__class__(model=self.model, query=query, using=self._db, hints=self._hints,
                               table_id=self.table_id)
        clone._for_write = self._for_write
        clone._prefetch_related_lookups = self._prefetch_related_lookups
        clone._known_related_objects = self._known_related_objects
        clone._iterable_class = self._iterable_class
        clone._fields = self._fields
        clone.definitions = self.definitions

        clone.__dict__.update(kwargs)
        return clone

    def get_definitions(self, table_id=-1):
        from shared_schema_tenants_custom_data.models import TenantSpecificFieldDefinition, TenantSpecificTable
        if not hasattr(self, 'definitions'):
            if self.model.__name__ == 'TenantSpecificTableRow':
                self.definitions = TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                    table_id=table_id)
            else:
                self.definitions = TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=ContentType.objects.get_for_model(self.model))
        return self.definitions

    def update(self, *args, **kwargs):
        from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
            _get_pivot_table_class_for_data_type)
        definitions = self.get_definitions()
        definitions_by_name = {d.name: d for d in definitions}

        custom_fields = {k: v for k, v in kwargs.items() if k in definitions_by_name.keys()}
        common_fields = {k: v for k, v in kwargs.items() if k not in definitions_by_name.keys()}

        super(TenantSpecificFieldsQueryset, self).update(**common_fields)

        for field_name, field_value in custom_fields.items():
            PivotTableClass = _get_pivot_table_class_for_data_type(definitions_by_name[field_name].data_type)
            (PivotTableClass.objects
             .filter(definition__id=definitions_by_name[field_name].id)
             .update(value=field_value))
