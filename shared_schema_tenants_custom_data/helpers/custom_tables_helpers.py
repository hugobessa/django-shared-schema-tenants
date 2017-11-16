

def get_custom_table_manager(table_name):
    from shared_schema_tenants_custom_data.models import TenantSpecificTable, TenantSpecificTableRow
    from shared_schema_tenants_custom_data.managers import TenantSpecificTableRowManager
    table = TenantSpecificTable.objects.get(name=table_name)
    manager = TenantSpecificTableRowManager()
    manager.model = TenantSpecificTableRow
    manager.table_id = table.id
    return manager


def _get_pivot_table_class_for_data_type(data_type):
    from shared_schema_tenants_custom_data.models import (
        TenantSpecificFieldIntegerPivot,
        TenantSpecificFieldCharPivot,
        TenantSpecificFieldTextPivot,
        TenantSpecificFieldFloatPivot,
        TenantSpecificFieldDatePivot,
        TenantSpecificFieldDateTimePivot
    )

    if data_type == 'integer':
        return TenantSpecificFieldIntegerPivot
    elif data_type == 'char':
        return TenantSpecificFieldCharPivot
    elif data_type == 'text':
        return TenantSpecificFieldTextPivot
    elif data_type == 'float':
        return TenantSpecificFieldFloatPivot
    elif data_type == 'date':
        return TenantSpecificFieldDatePivot
    elif data_type == 'datetime':
        return TenantSpecificFieldDateTimePivot

