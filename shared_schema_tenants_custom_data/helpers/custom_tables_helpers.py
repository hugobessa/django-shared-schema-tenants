def get_custom_table_queryset(table_name):
    from shared_schema_tenants_custom_data.models import TenantSpecificTableRow
    return TenantSpecificTableRow.objects.filter(table__name=table_name)
