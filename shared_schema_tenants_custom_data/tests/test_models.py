from model_mommy import mommy
from django.contrib.contenttypes.models import ContentType


from tests.utils import SharedSchemaTenantsTestCase
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition)
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
    get_custom_table_manager, _get_pivot_table_class_for_data_type)


class TenantSpecificTableTests(SharedSchemaTenantsTestCase):

    def setUp(self):
        super(TenantSpecificTableTests, self).setUp()
        self.table = mommy.make('shared_schema_tenants_custom_data.TenantSpecificTable', tenant=self.tenant)
        self.fields = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition', table_id=self.table.id,
            table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
            data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, default_value='1',
            tenant=self.tenant, _quantity=10)

        self.row = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificTableRow', table=self.table, tenant=self.tenant)

        for i, field in enumerate(self.fields):
            PivotTableClass = _get_pivot_table_class_for_data_type(field.data_type)
            PivotTableClass.objects.filter(row_id=self.row.id, definition=field).update(value=i + 5)

    def test_can_filter_by_tenant_specific_fields(self):
        row = get_custom_table_manager(self.table.name).all().first()

        for i, field in enumerate(self.fields):
            self.assertEqual(getattr(row, field.name, None), i + 5)

    def test_filter_by_tenant_specific_field(self):
        for i, field in enumerate(self.fields):
            rows = get_custom_table_manager(self.table.name).filter(**{field.name: i + 5})
            self.assertEqual(rows.count(), 1)

    def test_exclude_by_tenant_specific_field(self):
        for i, field in enumerate(self.fields):
            rows = get_custom_table_manager(self.table.name).exclude(**{field.name: i + 5})
            self.assertEqual(rows.count(), 0)

    def test_filter_by_tenant_specific_field_with_lookup(self):
        for i, field in enumerate(self.fields):
            rows = get_custom_table_manager(self.table.name).filter(**{field.name + '__gte': i})
            self.assertEqual(rows.count(), 1)

    def test_create_row_with_specific_fields_values(self):
        field_value_dict = {}
        for i, field in enumerate(self.fields):
            field_value_dict[field.name] = i + 50

        get_custom_table_manager(self.table.name).create(**field_value_dict)

        for i, field in enumerate(self.fields):
            rows = get_custom_table_manager(self.table.name).filter(**{field.name: i + 50})
            self.assertEqual(rows.count(), 1)

        self.assertEqual(get_custom_table_manager(self.table.name).all().count(), 2)

    def test_update_row_with_specific_fields_values(self):
        field_value_dict = {}
        for i, field in enumerate(self.fields):
            field_value_dict[field.name] = i + 50

        (get_custom_table_manager(self.table.name)
         .filter(table_id=self.table.id, id=self.row.id)
         .update(**field_value_dict))

        for i, field in enumerate(self.fields):
            rows = get_custom_table_manager(self.table.name).filter(**{field.name: i + 50})
            self.assertEqual(rows.count(), 1)

        self.assertEqual(get_custom_table_manager(self.table.name).all().count(), 1)

