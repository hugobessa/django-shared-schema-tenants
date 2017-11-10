from django.db import models
from django.conf import settings
from shared_schema_tenants_custom_data.mixins import TenantSpecificFieldsModelMixin


class Lecture(TenantSpecificFieldsModelMixin):
    subject = models.CharField(max_length=100)
    description = models.TextField()
    speaker = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __str__(self):
        return '%s - %s' % (self.subject, self.speaker)
