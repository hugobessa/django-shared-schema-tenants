import urllib
from model_mommy import mommy
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse
from django.test import override_settings

from tests.utils import SharedSchemaTenantsAPITestCase
from exampleproject.lectures.models import Lecture
from shared_schema_tenants.helpers.tenants import set_current_tenant
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition)
from shared_schema_tenants_custom_data.serializers import (
    TenantSpecificFieldDefinitionCreateSerializer)
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
    get_custom_table_manager, _get_pivot_table_class_for_data_type)


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
                PivotTableClass = _get_pivot_table_class_for_data_type(field.data_type)
                PivotTableClass.objects.filter(
                    row_id=self.row.id, definition=field
                ).update(value=i + 5)
        self.client.force_authenticate(self.user)

        self.view_url = reverse('shared_schema_tenants_custom_data:custom_tables_list')
        validator_gt_2 = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldsValidator',
            module_path='shared_schema_tenants_custom_data.tests.validators.validator_gt_2')
        self.params = {
            'name': '_custom_tables__test_table_1',
            'fields_definitions': [
                {
                    'name': 'test1',
                    'data_type': 'integer',
                    'is_required': False,
                    'default_value': 3,
                    'validators': [validator_gt_2.id]
                },
                {
                    'name': 'test2',
                    'data_type': 'integer',
                    'is_required': False,
                    'default_value': 1,
                    'validators': []
                }
            ]
        }

    def test_correct_number_of_tables(self):
        response = self.client.get(
            self.view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['lectures.Lecture']
        }
    )
    def test_correct_number_of_tables_with_customizable_models(self):
        response = self.client.get(
            self.view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 11)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['lectures.Lecture']
        }
    )
    def test_search_results_correctly(self):
        get_params_dict = {
            'search': 'lecture',
        }
        try:
            get_params = urllib.parse.urlencode(get_params_dict, doseq=True)
        except AttributeError:
            get_params = urllib.urlencode(get_params_dict, doseq=True)

        response = self.client.get(
            self.view_url + '?' + get_params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['lectures.Lecture']
        }
    )
    def test_filters_custom_tables_results_correctly(self):
        get_params_dict = {
            'filter': '_custom_tables',
        }

        try:
            get_params = urllib.parse.urlencode(get_params_dict, doseq=True)
        except AttributeError:
            get_params = urllib.urlencode(get_params_dict, doseq=True)

        response = self.client.get(
            self.view_url + '?' + get_params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['lectures.Lecture']
        }
    )
    def test_filters_customizable_models_results_correctly(self):
        get_params_dict = {
            'filter': 'customizable_models',
        }

        try:
            get_params = urllib.parse.urlencode(get_params_dict, doseq=True)
        except AttributeError:
            get_params = urllib.urlencode(get_params_dict, doseq=True)

        response = self.client.get(
            self.view_url + '?' + get_params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    @override_settings(
        SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
            'CUSTOMIZABLE_MODELS': ['lectures.Lecture']
        }
    )
    def test_paginate_results_correctly(self):
        get_params_dict = {
            'page': 2,
            'length': 4,
        }

        try:
            get_params = urllib.parse.urlencode(get_params_dict, doseq=True)
        except AttributeError:
            get_params = urllib.urlencode(get_params_dict, doseq=True)

        response = self.client.get(
            self.view_url + '?' + get_params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 11)
        self.assertEqual(len(response.data['results']), 4)

    def test_create(self):
        response = self.client.post(
            self.view_url, self.params, format='json', HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, 201)
        set_current_tenant(self.tenant.slug)
        tables = TenantSpecificTable.objects.all()
        self.assertEqual(tables.count(), 11)
        new_table = tables.get(name=response.data['name'].split('__')[1])
        self.assertEqual(new_table.fields_definitions.count(), 2)


@override_settings(
    SHARED_SCHEMA_TENANTS_CUSTOM_DATA={
        'CUSTOMIZABLE_MODELS': ['lectures.Lecture']
    }
)
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
                PivotTableClass = _get_pivot_table_class_for_data_type(
                    field.data_type)
                PivotTableClass.objects.filter(
                    row_id=self.row.id, definition=field
                ).update(value=i + 5)

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
            kwargs={'slug': 'lectures__lecture'})

        self.client.force_authenticate(self.user)

        self.validator_gt_2 = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldsValidator',
            module_path='shared_schema_tenants_custom_data.tests.validators.validator_gt_2')
        self.params = {
            'name': '_custom_tables__test_table_1',
            'fields_definitions': [
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
                    'validators': [self.validator_gt_2.id]
                }
            ]
        }

    def test_retrieves_custom_table_correctly(self):
        response = self.client.get(
            self.custom_table_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], '_custom_tables__' + self.tables[0].name)
        self.assertEqual(len(response.data['fields_definitions']), 10)

    def test_retrieves_customizable_model_correctly(self):
        response = self.client.get(
            self.customizable_model_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['fields_definitions']), 10)
        self.assertEqual(
            TenantSpecificFieldDefinition.original_manager.filter(
                table_content_type=ContentType.objects.get_for_model(Lecture),
                tenant=self.tenant
            ).count(), 10)

    def test_updates_custom_table_correctly(self):
        updated_definitions = TenantSpecificFieldDefinitionCreateSerializer(
            self.tables[0].fields_definitions.first()).data
        params = {
            'name': self.params['name'],
            'fields_definitions': self.params['fields_definitions'] + [updated_definitions]
        }

        response = self.client.put(
            self.custom_table_view_url, params, format='json',
            HTTP_TENANT_SLUG=self.tenant.slug)

        set_current_tenant(self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['fields_definitions']), 3)
        self.assertEqual(self.tables[0].fields_definitions.count(), 3)

    def test_updates_customizable_model_correctly(self):
        updated_definitions = TenantSpecificFieldDefinitionCreateSerializer(
            self.lecture_fields[0]).data
        params = {
            'fields_definitions': self.params['fields_definitions'] + [updated_definitions]
        }

        response = self.client.put(
            self.customizable_model_view_url, params, format='json',
            HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['fields_definitions']), 3)
        self.assertEqual(
            TenantSpecificFieldDefinition.original_manager.filter(
                table_content_type=ContentType.objects.get_for_model(Lecture),
                tenant=self.tenant
            ).count(), 3)

    def test_destroys_custom_table_correctly(self):
        response = self.client.delete(self.custom_table_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

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
            PivotTableClass = _get_pivot_table_class_for_data_type(field.data_type)
            PivotTableClass.objects.filter(row_id=self.row.id, definition=field).update(value=i + 5)

        self.client.force_authenticate(self.user)

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

    def test_create_invalid(self):
        params = {}
        for i, field in enumerate(self.fields):
            if i == 0:
                validator_lt_2 = mommy.make(
                    'shared_schema_tenants_custom_data.TenantSpecificFieldsValidator',
                    module_path='shared_schema_tenants_custom_data.tests.validators.validator_lt_2')
                field.validators.add(validator_lt_2)
            params[field.name] = 1 + 1000

        response = self.client.post(
            self.list_view_url, params, format='json', HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 400)

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


class LecturesViewSetTests(SharedSchemaTenantsAPITestCase):

    def setUp(self):
        super(LecturesViewSetTests, self).setUp()
        self.validator_gt_2 = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldsValidator',
            module_path='shared_schema_tenants_custom_data.tests.validators.validator_gt_2')
        self.lecture_fields = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition',
            table_content_type=ContentType.objects.get_for_model(Lecture),
            data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, default_value='1',
            tenant=self.tenant, validators=[self.validator_gt_2], _quantity=2)

        lecture_fields_values = {
            lf.name: i + 100
            for i, lf in enumerate(self.lecture_fields)
        }
        self.lecture = mommy.make('lectures.Lecture', **lecture_fields_values)

        self.list_view_url = reverse('lectures:list')
        self.details_view_url = reverse(
            'lectures:details', kwargs={'pk': self.lecture.pk})

        self.client.force_authenticate(self.user)

        self.params = {
            'subject': "Test",
            'description': ("Lorem ipsum dolor sit amet consectetur adipisicing elit. "
                            "Recusandae, qui? Voluptate reprehenderit vel mollitia, "
                            "placeat et aperiam sit voluptatibus eum deserunt corrupti "
                            "nulla quidem nesciunt atque dicta, accusantium ipsam at?"),
            'speaker': self.user.id,
        }
        self.params.update({f.name: i + 1000 for i, f in enumerate(self.lecture_fields)})

    def test_list(self):
        response = self.client.get(
            self.list_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIn(self.lecture_fields[0].name, response.data[0].keys())
        self.assertIn(self.lecture_fields[1].name, response.data[0].keys())

    def test_retrieve(self):
        response = self.client.get(
            self.details_view_url, HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)

    def test_create(self):
        response = self.client.post(
            self.list_view_url, self.params, format='json', HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 201)

        set_current_tenant(self.tenant.slug)
        new_lecture = Lecture.objects.get(id=response.data['id'])
        for key, value in self.params.items():
            if key != 'speaker':
                self.assertEqual(getattr(new_lecture, key), value)
            else:
                self.assertEqual(getattr(new_lecture, key).pk, value)

    def test_create_invalid(self):
        self.params[self.lecture_fields[0].name] = -100
        response = self.client.post(
            self.list_view_url, self.params, format='json', HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 400)

    def test_update(self):
        response = self.client.put(
            self.details_view_url, self.params, format='json', HTTP_TENANT_SLUG=self.tenant.slug)

        self.assertEqual(response.status_code, 200)

        set_current_tenant(self.tenant.slug)
        updated_lecture = Lecture.objects.get(id=response.data['id'])
        for key, value in self.params.items():
            if key != 'speaker':
                self.assertEqual(getattr(updated_lecture, key), value)
            else:
                self.assertEqual(getattr(updated_lecture, key).pk, value)
