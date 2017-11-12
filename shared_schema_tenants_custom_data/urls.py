# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from shared_schema_tenants_custom_data import views

urlpatterns = [
    url(
        regex=r'^custom-tables/$',
        view=views.CustomizableModelsList.as_view(),
        name='custom_tables_list'
    ),
    url(
        regex=r'^custom-tables/(?P<slug>[\w.@+-]+)/$',
        view=views.CustomTableDetails.as_view(),
        name='custom_tables_details'
    ),
    url(
        regex=r'^(?P<slug>[\w.@+-]+)/$',
        view=views.TenantSpecificTableRowViewset.as_view({
            'get': 'list',
            'post': 'create',
        }),
        name='custom_data_list'
    ),
    url(
        regex=r'^(?P<slug>[\w.@+-]+)/(?P<pk>[\d]+)/$',
        view=views.TenantSpecificTableRowViewset.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='custom_data_details'
    ),
]
