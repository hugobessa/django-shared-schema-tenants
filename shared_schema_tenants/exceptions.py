

class TenantNotFoundError(Exception):

    def __init__(self, message, errors):
        super(Exception, self).__init__(message)


class TenantFieldTypeConfigurationError(Exception):

    def __init__(self, message, errors):
        super(Exception, self).__init__(message)
