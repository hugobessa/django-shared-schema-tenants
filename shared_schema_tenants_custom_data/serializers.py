from rest_framework import serializers
from shared_schema_tenants_custom_data.models import TenantSpecificFieldDefinition, TenantSpecificFieldChunk


class TenantSpecificFieldDefinitionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TenantSpecificFieldDefinition
        fields = ['id', 'name', 'data_type', 'is_required', 'default_value', 'validators']

    def create(self, validated_date):
        table_content_type = self.context['table_content_type']
        table_id = self.context.get('table_id')

        return TenantSpecificFieldDefinition.objects.create(
            table_content_type=table_content_type,
            table_id=table_id,
            **validated_date
        )


class TenantSpecificFieldDefinitionUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TenantSpecificFieldDefinition
        fields = ['id', 'is_required', 'default_value', 'validators']

    def validate(self, data):
        if TenantSpecificFieldChunk.objects.filter(data['id']).exists():
            is_required = data.get('is_required', self.instance.is_required)
            default_value = data.get('default_value', self.instance.defaul_value)

            if is_required and not default_value:
                raise serializers.ValidationError(_(
                    'Your table already has data, so a new field must either be not required '
                    'or have a default value'))

        return data

    def update(self, instance, validated_date):
        instance.is_required = validated_date.get('is_required', instance.is_required)
        instance.default_value = validated_date.get('default_value', instance.default_value)
        instance.save()

        instance.validators.set(validated_date.get('validators', instance.validators))

        return instance
