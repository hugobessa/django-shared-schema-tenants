from rest_framework import serializers
from shared_schema_tenants_custom_data.serializers import TenantSpecificModelSerializer

from .models import Lecture


class LectureSerializer(TenantSpecificModelSerializer):
    speaker_name = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = ['id', 'subject', 'speaker', 'speaker_name', 'description']

    def get_speaker_name(self, obj):
        return obj.speaker.first_name + ' ' + obj.speaker.last_name
