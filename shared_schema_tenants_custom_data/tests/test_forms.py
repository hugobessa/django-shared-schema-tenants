from model_mommy import mommy
from django.contrib.contenttypes.models import ContentType

from tests.utils import SharedSchemaTenantsAPITestCase
from shared_schema_tenants.helpers.tenants import set_current_tenant
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition, TenantSpecificFieldChunk)
from shared_schema_tenants_custom_data.forms import get_tenant_specific_table_row_form_class
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import get_custom_table_manager


class TenantSpecificTableRowViewsetTests(SharedSchemaTenantsAPITestCase):

    def setUp(self):
        super(TenantSpecificTableRowViewsetTests, self).setUp()
        self.table = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificTable', tenant=self.tenant)
        self.fields = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition', table_id=self.table.id,
            table_content_type=ContentType.objects.get_for_model(
                TenantSpecificTable),
            data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, default_value='1',
            tenant=self.tenant, _quantity=10)

        self.row = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificTableRow', table=self.table, tenant=self.tenant)

        for i, field in enumerate(self.fields):
            field_value_dict = {'value_' + field.data_type: i + 5}
            TenantSpecificFieldChunk.objects.filter(
                row_id=self.row.id, definition=field).update(**field_value_dict)

        self.params = {field.name: i + 1000 for i, field in enumerate(self.fields)}
        set_current_tenant(self.tenant.slug)

    def test_create(self):
        form = get_tenant_specific_table_row_form_class(self.table.name)(data=self.params)
        self.assertTrue(form.is_valid())

        instance = form.save()

        self.assertEqual(get_custom_table_manager(
            self.table.name).all().count(), 2)

        for key, value in self.params.items():
            self.assertEqual(
                getattr(instance, key),
                value
            )

    def test_update(self):
        form = get_tenant_specific_table_row_form_class(self.table.name)(instance=self.row, data=self.params)
        self.assertTrue(form.is_valid())
        form.save()
        updated_row = get_custom_table_manager(self.table.name).get(id=self.row.id)
        for key, value in self.params.items():
            self.assertEqual(
                getattr(updated_row, key),
                value
            )
