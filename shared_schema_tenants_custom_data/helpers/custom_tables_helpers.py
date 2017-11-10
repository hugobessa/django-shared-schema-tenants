def get_custom_table_manager(table_name):
    from shared_schema_tenants_custom_data.models import TenantSpecificTable, TenantSpecificTableRow
    from shared_schema_tenants_custom_data.managers import TenantSpecificTableRowManager
    table = TenantSpecificTable.objects.get(name=table_name)
    manager = TenantSpecificTableRowManager()
    manager.model = TenantSpecificTableRow
    manager.table_id = table.id
    return manager
