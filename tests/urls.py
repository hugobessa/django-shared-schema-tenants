# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url, include

from shared_schema_tenants.urls import urlpatterns as shared_schema_tenants_urls
from shared_schema_tenants_custom_data.urls import (
    urlpatterns as shared_schema_tenants_custom_data_urls)
from exampleproject.lectures.urls import urlpatterns as lectures_urls

urlpatterns = [
    url(r'^lectures/', include(lectures_urls, namespace='lectures')),
    url(r'^', include(shared_schema_tenants_urls, namespace='shared_schema_tenants')),
    url(r'^', include(shared_schema_tenants_custom_data_urls,
        namespace='shared_schema_tenants_custom_data')),
]
