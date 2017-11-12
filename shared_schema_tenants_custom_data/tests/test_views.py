import urllib
from model_mommy import mommy
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse
from django.test import override_settings

from tests.utils import SharedSchemaTenantsAPITestCase
from exampleproject.example_custom_data.models import Lecture
from shared_schema_tenants.helpers.tenants import set_current_tenant
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition, TenantSpecificFieldChunk)
from shared_schema_tenants_custom_data.serializers import (
    TenantSpecificFieldDefinitionCreateSerializer)
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import get_custom_table_manager


class CustomTablesListTests(SharedSchemaTenantsAPITestCase):

    def setUp(self):
        super(CustomTablesListTests, self).setUp()
        self.tables = mommy.make('shared_schema_tenants_custom_data.TenantSpecificTable',
                                 tenant=self.tenant, _quantity=10)

        for table in self.tables:
            self.fields = mommy.make(
                'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition', table_id=table.id,
                table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, default_value='1',
                tenant=self.tenant, _quantity=10)
        for table in self.tables:
            self.row = mommy.make(
                'shared_schema_tenants_custom_data.TenantSpecificTableRow', table=table, tenant=self.tenant)

            for i, field in enumerate(self.fields):
                field_value_dict = {'value_' + field.data_type: i + 5}
                TenantSpecificFieldChunk.objects.filter(
                    row_id=self.row.id, definition=field
                ).update(**field_value_dict)

        self.view_url = reverse('shared_schema_tenants_custom_data:custom_tables_list')

    def test_correct_number_of_tables(self):
        response = self.client.get(
            self.view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['example_custom_data.Lecture']
        }
    )
    def test_correct_number_of_tables_with_customizable_models(self):
        response = self.client.get(
            self.view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 11)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['example_custom_data.Lecture']
        }
    )
    def test_search_results_correctly(self):
        get_params_dict = {
            'search': 'lecture',
        }

        get_params = urllib.parse.urlencode(get_params_dict, doseq=True)

        response = self.client.get(
            self.view_url + '?' + get_params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['example_custom_data.Lecture']
        }
    )
    def test_filters_custom_tables_results_correctly(self):
        get_params_dict = {
            'filter': '_custom_tables',
        }

        get_params = urllib.parse.urlencode(get_params_dict, doseq=True)

        response = self.client.get(
            self.view_url + '?' + get_params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['example_custom_data.Lecture']
        }
    )
    def test_filters_customizable_models_results_correctly(self):
        get_params_dict = {
            'filter': 'customizable_models',
        }

        get_params = urllib.parse.urlencode(get_params_dict, doseq=True)

        response = self.client.get(
            self.view_url + '?' + get_params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['example_custom_data.Lecture']
        }
    )
    def test_paginate_results_correctly(self):
        get_params_dict = {
            'page': 2,
            'length': 4,
        }

        get_params = urllib.parse.urlencode(get_params_dict, doseq=True)

        response = self.client.get(
            self.view_url + '?' + get_params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 11)
        self.assertEqual(len(response.data['results']), 4)


class CustomTablesDetailsTests(SharedSchemaTenantsAPITestCase):

    def setUp(self):
        super(CustomTablesDetailsTests, self).setUp()
        self.tables = mommy.make('shared_schema_tenants_custom_data.TenantSpecificTable',
                                 tenant=self.tenant, _quantity=10)

        for table in self.tables:
            fields = mommy.make(
                'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition', table_id=table.id,
                table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, default_value='1',
                tenant=self.tenant, _quantity=10)

            self.row = mommy.make(
                'shared_schema_tenants_custom_data.TenantSpecificTableRow', table=table, tenant=self.tenant)

            for i, field in enumerate(fields):
                field_value_dict = {'value_' + field.data_type: i + 5}
                TenantSpecificFieldChunk.objects.filter(
                    row_id=self.row.id, definition=field
                ).update(**field_value_dict)

        self.lecture_fields = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition',
            table_content_type=ContentType.objects.get_for_model(Lecture),
            data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, default_value='1',
            tenant=self.tenant, _quantity=10)

        self.custom_table_view_url = reverse(
            'shared_schema_tenants_custom_data:custom_tables_details',
            kwargs={'slug': '_custom_tables__' + self.tables[0].name})
        self.customizable_model_view_url = reverse(
            'shared_schema_tenants_custom_data:custom_tables_details',
            kwargs={'slug': 'example_custom_data__lecture'})

        self.params = [
            {
                'name': 'test1',
                'data_type': 'integer',
                'is_required': False,
                'default_value': 1,
                'validators': []
            },
            {
                'name': 'test2',
                'data_type': 'integer',
                'is_required': False,
                'default_value': 1,
                'validators': []
            }
        ]

    def test_retrieves_custom_table_correctly(self):
        response = self.client.get(
            self.custom_table_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)

    def test_retrieves_customizable_model_correctly(self):
        response = self.client.get(
            self.customizable_model_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)
        self.assertEqual(
            TenantSpecificFieldDefinition.original_manager.filter(
                table_content_type=ContentType.objects.get_for_model(Lecture),
                tenant=self.tenant
            ).count(), 10)

    def test_updates_custom_table_correctly(self):
        updated_definitions = TenantSpecificFieldDefinitionCreateSerializer(
            self.tables[0].fields_definitions.first()).data
        params = self.params + [updated_definitions]

        response = self.client.put(
            self.custom_table_view_url, params, format='json',
            HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            TenantSpecificFieldDefinition.original_manager.filter(
                table_id=self.tables[0].id,
                table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                tenant=self.tenant
            ).count(), 2)

    def test_updates_customizable_model_correctly(self):
        updated_definitions = TenantSpecificFieldDefinitionCreateSerializer(
            self.lecture_fields[0]).data
        params = self.params + [updated_definitions]

        response = self.client.put(
            self.customizable_model_view_url, params, format='json',
            HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            TenantSpecificFieldDefinition.original_manager.filter(
                table_content_type=ContentType.objects.get_for_model(Lecture),
                tenant=self.tenant
            ).count(), 2)

    def test_destroys_custom_table_correctly(self):
        response = self.client.put(
            self.custom_table_view_url, format='json',
            HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TenantSpecificTable.objects.filter(id=self.tables[0].id).exists())
        self.assertEqual(
            TenantSpecificFieldDefinition.original_manager.filter(
                table_id=self.tables[0].id,
                table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                tenant=self.tenant
            ).count(), 0)

    def test_destroys_customizable_model_correctly(self):
        response = self.client.delete(
            self.customizable_model_view_url, format='json',
            HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            TenantSpecificFieldDefinition.original_manager.filter(
                table_content_type=ContentType.objects.get_for_model(Lecture),
                tenant=self.tenant
            ).count(), 0)


class TenantSpecificTableRowViewsetTests(SharedSchemaTenantsAPITestCase):

    def setUp(self):
        super(TenantSpecificTableRowViewsetTests, self).setUp()
        self.table = mommy.make('shared_schema_tenants_custom_data.TenantSpecificTable', tenant=self.tenant)
        self.fields = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition', table_id=self.table.id,
            table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
            data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, default_value='1',
            tenant=self.tenant, _quantity=10)

        self.row = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificTableRow', table=self.table, tenant=self.tenant)

        for i, field in enumerate(self.fields):
            field_value_dict = {'value_' + field.data_type: i + 5}
            TenantSpecificFieldChunk.objects.filter(row_id=self.row.id, definition=field).update(**field_value_dict)

        self.list_view_url = reverse(
            'shared_schema_tenants_custom_data:custom_data_list',
            kwargs={
                'slug': '_custom_tables__' + self.table.name,
            })
        self.details_view_url = reverse(
            'shared_schema_tenants_custom_data:custom_data_details',
            kwargs={
                'slug': '_custom_tables__' + self.table.name,
                'pk': self.row.id,
            })

    def test_list(self):
        response = self.client.get(
            self.list_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create(self):
        params = {}
        for i, field in enumerate(self.fields):
            params[field.name] = 1 + 1000

        response = self.client.post(
            self.list_view_url, params, format='json', HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 201)
        set_current_tenant(self.tenant.slug)
        self.assertEqual(get_custom_table_manager(self.table.name).all().count(), 2)

    def test_retrieve(self):
        response = self.client.get(
            self.details_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)

    def test_update(self):
        params = {}
        for i, field in enumerate(self.fields):
            params[field.name] = 1 + 1000

        response = self.client.put(
            self.details_view_url, params, format='json', HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        set_current_tenant(self.tenant.slug)
        for key, value in params.items():
            self.assertEqual(
                getattr(get_custom_table_manager(self.table.name).get(id=self.row.id), key),
                value)
