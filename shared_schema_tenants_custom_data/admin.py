from django.contrib import admin
from shared_schema_tenants_custom_data.forms import TenantSpecificModelForm
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition, TenantSpecificTableRow, TenantSpecificFieldsValidator)


class TenantSpecificModelAdmin(admin.ModelAdmin):
    form = TenantSpecificModelForm


admin.sites.register(TenantSpecificTable)
admin.sites.register(TenantSpecificFieldDefinition)
admin.sites.register(TenantSpecificTableRow)
admin.sites.register(TenantSpecificFieldsValidator)
