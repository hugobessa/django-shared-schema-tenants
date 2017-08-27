from django.db import models
from django.conf import settings
from shared_schema_tenants.mixins import (
    SingleTenantModelMixin, MultipleTenantsModelMixin)


class Article(SingleTenantModelMixin):
    title = models.CharField(max_length=100)
    text = models.TextField()
    tags = models.ManyToManyField('Tag')
    author = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __str__(self):
        return '%s - %s' % (self.title, str(self.author))


class Tag(MultipleTenantsModelMixin):
    text = models.CharField(max_length=100)

    def __str__(self):
        return self.text
