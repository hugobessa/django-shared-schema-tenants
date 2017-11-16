from django.db import models
from django.db.models.manager import BaseManager
from django.utils.version import get_complete_version

from django.contrib.contenttypes.models import ContentType

from shared_schema_tenants.managers import SingleTenantModelManager
from shared_schema_tenants_custom_data.querysets import TenantSpecificFieldsQueryset
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
    _get_pivot_table_class_for_data_type)


class TenantSpecificFieldsModelBaseManager(BaseManager):
    @classmethod
    def _get_queryset_methods(cls, queryset_class):
        import inspect
        from django.utils import six

        def create_method(name, method):
            def manager_method(self, *args, **kwargs):
                if self.model.__name__ == 'TenantSpecificTableRow':
                    table_id = getattr(self, 'table_id', None)
                    kwargs['table_id'] = table_id
                    return getattr(self.get_queryset(table_id=table_id), name)(*args, **kwargs)
                return getattr(self.get_queryset(), name)(*args, **kwargs)
            manager_method.__name__ = method.__name__
            manager_method.__doc__ = method.__doc__
            return manager_method

        new_methods = {}
        # Refs http://bugs.python.org/issue1785.
        predicate = inspect.isfunction if six.PY3 else inspect.ismethod
        for name, method in inspect.getmembers(queryset_class, predicate=predicate):
            # Only copy missing methods.
            if hasattr(cls, name):
                continue
            # Only copy public methods or methods with the attribute `queryset_only=False`.
            queryset_only = getattr(method, 'queryset_only', None)
            if queryset_only or (queryset_only is None and name.startswith('_')):
                continue
            # Copy the method onto the manager.
            new_methods[name] = create_method(name, method)
        return new_methods


class TenantSpecificFieldsModelManager(
        TenantSpecificFieldsModelBaseManager.from_queryset(TenantSpecificFieldsQueryset)):
    data_type_fields = {
        'integer': models.IntegerField(),
        'char': models.CharField(max_length=255),
        'text': models.TextField(),
        'float': models.FloatField(),
        'datetime': models.DateTimeField(),
        'date': models.DateField(),
    }

    def get_queryset(self, *args, **kwargs):
        from shared_schema_tenants_custom_data.models import TenantSpecificTableRow

        if self.model != TenantSpecificTableRow:
            kwargs.pop('table_id', None)
        else:
            if not hasattr(self, 'table_id'):
                self.table_id = kwargs.get('table_id', -1)
            else:
                kwargs['table_id'] = self.table_id

        custom_fields_annotations = self._get_custom_fields_annotations()
        queryset = super(TenantSpecificFieldsModelManager, self).get_queryset(*args, **kwargs)

        if len(custom_fields_annotations.keys()) > 0:
            if self.model == TenantSpecificTableRow:
                return (
                    queryset
                    .annotate(**custom_fields_annotations)
                    .filter(table_id=self.table_id)
                )
            return queryset.annotate(**custom_fields_annotations)

        if self.model == TenantSpecificTableRow:
            return queryset.filter(table_id=self.table_id)
        return queryset

    def _get_custom_fields_annotations(self):
        from shared_schema_tenants_custom_data.models import (
            TenantSpecificFieldDefinition, TenantSpecificTable, TenantSpecificTableRow)

        if self.model == TenantSpecificTableRow:
            definitions = TenantSpecificFieldDefinition.objects.filter(
                table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                table_id=self.table_id)
        else:
            definitions = TenantSpecificFieldDefinition.objects.filter(
                table_content_type=ContentType.objects.get_for_model(self.model))
        definitions_by_name = {d.name: d for d in definitions}

        custom_fields_annotations = {}

        for key, definition in definitions_by_name.items():
            if get_complete_version()[1] >= 11:
                from django.db.models import Subquery, OuterRef
                definitions_values = (
                    _get_pivot_table_class_for_data_type(definition.data_type).objects
                    .filter(definition__id=definition.id, row_id=OuterRef('pk'))
                    .values('value')
                )

                custom_fields_annotations[key] = Subquery(
                    queryset=definitions_values,
                    output_field=self.data_type_fields[definition.data_type]
                )
            else:
                from django.db.models.expressions import RawSQL
                model_content_type = ContentType.objects.get_for_model(self.model)
                model_table_name = (model_content_type.app_label + '_' + model_content_type.model)
                PivotTableClass = _get_pivot_table_class_for_data_type(definition.data_type)
                pivot_table_name = PivotTableClass._meta.db_table
                custom_fields_annotations[key] = RawSQL(
                    """
                        select p.value
                        from """ + pivot_table_name + """ p
                        where definition_id = %s and
                            p.row_id = """ + '"' + model_table_name + '"."' + self.model._meta.pk.name + '"',
                    [definition.id],
                    output_field=self.data_type_fields[definition.data_type])

        return custom_fields_annotations


class ManagerPassesTableIdToQueryset(models.Manager):

    def get_queryset(self, table_id=-1):
        return self._queryset_class(model=self.model, using=self._db, hints=self._hints, table_id=self.table_id)


class TenantSpecificTableRowManager(TenantSpecificFieldsModelManager, SingleTenantModelManager,
                                    ManagerPassesTableIdToQueryset):
    pass
