from django.core.exceptions import ValidationError
import mock

from tests.utils import SharedSchemaTenantsTestCase
from tests.settings import is_url
from shared_schema_tenants.exceptions import TenantFieldTypeConfigurationError
from shared_schema_tenants.helpers.tenant_json_field import TenantJSONFieldHelper


class TenantJSONFieldHelperTests(SharedSchemaTenantsTestCase):

    def setUp(self):
        super().setUp()
        self.tenant_json_field_helper = TenantJSONFieldHelper(
            instance_field_name='settings',
            tenant_fields={
                'logo': {
                    'type': 'string',
                    'validators': [is_url],
                },
                'number_of_employees': {
                    'type': 'number',
                    'required': True
                },
                'is_non_profit': {
                    'type': 'boolean',
                },
            },
            tenant_default_fields_values={
                'logo': None,
                'number_of_employees': 0,
                'is_non_profit': False,
            }
        )

    def test_validate_field_with_valid_value(self):
        validated_value = self.tenant_json_field_helper.validate_field({}, 'logo', 'http://test.url/image.jpg')

        self.assertEqual(validated_value, 'http://test.url/image.jpg')

    def test_validate_field_with_invalid_value(self):
        with self.assertRaises(ValidationError):
            self.tenant_json_field_helper.validate_field({}, 'logo', 'invalid value')

    def test_validate_field_with_wrong_type_value(self):
        with self.assertRaises(ValidationError):
            self.tenant_json_field_helper.validate_field({}, 'logo', 123)

    def test_validate_field_with_none_in_required_field(self):
        with self.assertRaises(ValidationError):
            self.tenant_json_field_helper.validate_field({}, 'number_of_employees', None)

    def test_validate_field_with_invalid_key(self):
        with self.assertRaises(ValidationError):
            self.tenant_json_field_helper.validate_field({}, 'invalid_key', 'dont_care')

    def test_validate_field_with_invalid_field_configuration_missing_type(self):
        tenant_json_field_helper = TenantJSONFieldHelper(
            instance_field_name='settings',
            tenant_fields={
                'logo': {}
            },
            tenant_default_fields_values={
                'logo': None,
            }
        )

        with self.assertRaises(TenantFieldTypeConfigurationError):
            tenant_json_field_helper.validate_field(
                {}, 'logo', 'http://test.url/image.jpg')

    def test_validate_field_with_invalid_field_type_configuration(self):
        tenant_json_field_helper = TenantJSONFieldHelper(
            instance_field_name='settings',
            tenant_fields={
                'logo': {
                    'type': 'invalid_field',
                    'validators': [is_url],
                }
            },
            tenant_default_fields_values={
                'logo': None,
            }
        )

        with self.assertRaises(TenantFieldTypeConfigurationError):
            tenant_json_field_helper.validate_field(
                {}, 'logo', 'http://test.url/image.jpg')

    @mock.patch('shared_schema_tenants.helpers.tenant_json_field.TenantJSONFieldHelper.validate_field')
    def test_validate_fields_calls_validate_field(self, validate_field):
        tenant_json_field_helper = TenantJSONFieldHelper(
            instance_field_name='settings',
            tenant_fields={
                'logo': {
                    'type': 'string',
                    'validators': [is_url],
                },
                'number_of_employees': {
                    'type': 'number',
                    'required': True
                },
            },
            tenant_default_fields_values={
                'logo': None,
                'number_of_employees': 0,
            }
        )

        tenant_json_field_helper.validate_fields(
            {}, {'logo': 'http://test.url/image.jpg', 'number_of_employees': 10}, partial=False)

        validate_field.assert_has_calls([
            mock.call({}, 'logo', 'http://test.url/image.jpg',
                      self.tenant.settings.get('logo')),
        ])
        validate_field.assert_has_calls([
            mock.call({}, 'number_of_employees', 10,
                      self.tenant.settings.get('number_of_employees')),
        ])

    @mock.patch('shared_schema_tenants.helpers.tenant_json_field.TenantJSONFieldHelper.validate_field')
    def test_validate_fields_partial_calls_validate_field_once(self, validate_field):
        tenant_json_field_helper = TenantJSONFieldHelper(
            instance_field_name='settings',
            tenant_fields={
                'logo': {
                    'type': 'string',
                    'validators': [is_url],
                },
                'number_of_employees': {
                    'type': 'number',
                    'required': True
                },
            },
            tenant_default_fields_values={
                'logo': None,
                'number_of_employees': 0,
            }
        )

        tenant_json_field_helper.validate_fields(
            {}, {'logo': 'http://test.url/image.jpg'}, partial=True)

        validate_field.assert_called_once()

    @mock.patch('shared_schema_tenants.helpers.tenant_json_field.TenantJSONFieldHelper.validate_field')
    def test_validate_fields_missing_one_field_calls_validate_field(self, validate_field):
        tenant_json_field_helper = TenantJSONFieldHelper(
            instance_field_name='settings',
            tenant_fields={
                'logo': {
                    'type': 'string',
                    'validators': [is_url],
                },
                'number_of_employees': {
                    'type': 'number',
                    'required': True
                },
            },
            tenant_default_fields_values={
                'logo': None,
                'number_of_employees': 0,
            }
        )

        tenant_json_field_helper.validate_fields(
            {}, {'logo': 'http://test.url/image.jpg'})

        validate_field.assert_has_calls([
            mock.call({}, 'logo', 'http://test.url/image.jpg',
                      self.tenant.settings.get('logo')),
        ])
        validate_field.assert_has_calls([
            mock.call({}, 'number_of_employees', None,
                      self.tenant.settings.get('number_of_employees')),
        ])
