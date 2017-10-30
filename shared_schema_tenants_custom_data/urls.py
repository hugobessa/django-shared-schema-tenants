# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^custom-tables/$',
        view=views.CustomizableModelsList.as_view(),
        name='tenant_list'
    ),
    url(
        regex=r'^custom-tables/(?P<slug>[\w.@+-]+)/$',
        view=views.CustomTableDetails.as_view(),
        name='tenant_details'
    ),

]
