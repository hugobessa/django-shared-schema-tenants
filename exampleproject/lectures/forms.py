from shared_schema_tenants_custom_data.forms import TenantSpecificModelForm
from .models import Lecture


class LectureForm(TenantSpecificModelForm):

    class Meta:
        model = Lecture
        fields = ['id', 'subject', 'speaker', 'description']
