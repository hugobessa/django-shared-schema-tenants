import mock
from django.test import TestCase
from django.core.exceptions import ValidationError

from shared_schema_tenants.validators import validate_json


class ValidateJsonTests(TestCase):

    @mock.patch('shared_schema_tenants.validators.json.loads')
    def test_valid_json(self, json_loads):
        validate_json('10')
        json_loads.assert_called_once()

    def test_invalid_json(self):
        with self.assertRaises(ValidationError):
            validate_json('{')

