

class TenantNotFoundError(Exception):

    def __init__(self, message="Tenant with this slug couldn't be found", errors=[]):
        super(TenantNotFoundError, self).__init__(message)


class TenantFieldTypeConfigurationError(Exception):

    def __init__(self, message="The field is not configured correctly", errors=[]):
        super(TenantFieldTypeConfigurationError, self).__init__(message)
