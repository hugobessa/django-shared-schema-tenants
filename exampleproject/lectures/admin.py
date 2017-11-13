from django.contrib import admin
from shared_schema_tenants_custom_data.admin import TenantSpecificModelAdmin

from .models import Lecture


class LectureAdmin(TenantSpecificModelAdmin):
    pass


admin.sites.register(Lecture, LectureAdmin)
