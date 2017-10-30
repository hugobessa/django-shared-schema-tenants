from django.test import TestCase
from shared_schema_tenants.utils import import_class


class ImportClassTests(TestCase):

    def test_class_is_really_imported(self):
        TenantSettingsHelper = import_class(
            'shared_schema_tenants.helpers.tenant_settings.TenantSettingsHelper')

        self.assertEqual(TenantSettingsHelper.__name__, 'TenantSettingsHelper')
