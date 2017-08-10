# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^organization/$',
        view=views.TenantListView.as_view(),
        name='tenant_list'
    ),
    url(
        regex=r'^organization/(?P<pk>[\w.@+-]+)/$',
        view=views.TenantDetailsView.as_view(),
        name='tenant_details'
    ),
    url(
        regex=r'^organization-site/$',
        view=views.TenantSiteListView.as_view(),
        name='tenant_site_list'
    ),
    url(
        regex=r'^organization-site/(?P<pk>[\d]+)/$',
        view=views.TenantSiteDetailsView.as_view(),
        name='tenant_site_details'
    ),
]
