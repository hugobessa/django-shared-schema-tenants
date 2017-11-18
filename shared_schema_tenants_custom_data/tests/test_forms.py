from model_mommy import mommy
from django.contrib.contenttypes.models import ContentType

from tests.utils import SharedSchemaTenantsAPITestCase
from shared_schema_tenants.helpers.tenants import set_current_tenant
from exampleproject.lectures.models import Lecture
from exampleproject.lectures.forms import LectureForm
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition)
from shared_schema_tenants_custom_data.forms import get_tenant_specific_table_row_form_class
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
    get_custom_table_manager, _get_pivot_table_class_for_data_type)


class TenantSpecificTableRowFormTests(SharedSchemaTenantsAPITestCase):

    def setUp(self):
        super(TenantSpecificTableRowFormTests, self).setUp()
        self.table = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificTable', tenant=self.tenant)
        self.validator_gt_2 = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldsValidator',
            module_path='shared_schema_tenants_custom_data.tests.validators.validator_gt_2')
        self.fields = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificFieldDefinition', table_id=self.table.id,
            table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
            data_type=TenantSpecificFieldDefinition.DATA_TYPES.integer, default_value='1',
            tenant=self.tenant, validators=[self.validator_gt_2], _quantity=10)

        self.row = mommy.make(
            'shared_schema_tenants_custom_data.TenantSpecificTableRow', table=self.table, tenant=self.tenant)

        for i, field in enumerate(self.fields):
            PivotTableClass = _get_pivot_table_class_for_data_type(field.data_type)
            PivotTableClass.objects.filter(
                row_id=self.row.id, definition=field).update(value=i + 5)

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

    def test_create_invalid(self):
        self.params[self.fields[0].name] = -100
        form = get_tenant_specific_table_row_form_class(self.table.name)(data=self.params)
        self.assertFalse(form.is_valid())

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


class LectureFormTests(SharedSchemaTenantsAPITestCase):

    def setUp(self):
        super(LectureFormTests, self).setUp()
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

        self.params = {
            'subject': 'T'
        }
        self.params = {
            'subject': "Test",
            'description': ("Lorem ipsum dolor sit amet consectetur adipisicing elit. "
                            "Recusandae, qui? Voluptate reprehenderit vel mollitia, "
                            "placeat et aperiam sit voluptatibus eum deserunt corrupti "
                            "nulla quidem nesciunt atque dicta, accusantium ipsam at?"),
            'speaker': self.user.id,
        }
        self.params.update({field.name: i + 1000 for i, field in enumerate(self.lecture_fields)})
        set_current_tenant(self.tenant.slug)

    def test_create(self):
        form = LectureForm(data=self.params)
        self.assertTrue(form.is_valid())

        instance = form.save()

        self.assertEqual(Lecture.objects.all().count(), 2)

        for key, value in self.params.items():
            if key != 'speaker':
                self.assertEqual(
                    getattr(instance, key),
                    value
                )
            else:
                self.assertEqual(getattr(instance, key).pk, value)

    def test_create_invalid(self):
        self.params[self.lecture_fields[0].name] = -100
        form = LectureForm(data=self.params)
        self.assertFalse(form.is_valid())

    def test_update(self):
        form = LectureForm(instance=self.lecture, data=self.params)
        self.assertTrue(form.is_valid())
        form.save()
        updated_lecture = Lecture.objects.get(id=self.lecture.id)
        for key, value in self.params.items():
            if key != 'speaker':
                self.assertEqual(
                    getattr(updated_lecture, key),
                    value
                )
            else:
                self.assertEqual(getattr(updated_lecture, key).pk, value)
