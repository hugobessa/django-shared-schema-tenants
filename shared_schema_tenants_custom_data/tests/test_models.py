from model_mommy import mommy
from django.contrib.contenttypes.models import ContentType


from tests.utils import SharedSchemaTenantsTestCase
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition, TenantSpecificTableRow)


class TenantSpecificTableTests(SharedSchemaTenantsTestCase):

    def setUp(self):
        super(TenantSpecificTableTests, self).setUp()
        self.table = mommy.make('shared_schema_tenants_custom_data.TenantSpecificTable', tenant=self.tenant)
        self.fields = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition', table_id=self.table.id,
            table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
            data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, tenant=self.tenant, _quantity=10)

        self.row = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificTableRow', table=self.table, tenant=self.tenant)

        for i, field in enumerate(self.fields):
            field_value_dict = {'value_' + field.data_type: i + 5}
            mommy.make(
                'shared_schema_tenants_custom_data.TenantSpecificFieldChunk', definition=field,
                row=self.row, tenant=self.tenant, **field_value_dict)

    def test_can_filter_by_tenant_specific_fields(self):
        row = TenantSpecificTableRow.objects.get_queryset(table_id=self.table.id).all().first()

        for i, field in enumerate(self.fields):
            self.assertEqual(getattr(row, field.name, None), i + 5)

