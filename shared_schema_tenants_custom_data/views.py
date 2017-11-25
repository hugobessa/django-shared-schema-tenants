from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from shared_schema_tenants.utils import import_from_string
from shared_schema_tenants_custom_data.permissions import DjangoTenantSpecificTablePermissions
from shared_schema_tenants_custom_data.settings import get_setting
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition)
from shared_schema_tenants_custom_data.serializers import (
    get_tenant_specific_table_row_serializer_class, TenantSpecificTableSerializer,
    TenantSpecificFieldsModelDefinitionsUpdateSerializer)
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import get_custom_table_manager


class CustomizableModelsList(APIView):

    def get_permissions(self):
        return [
            import_from_string(permission)()
            for permission in get_setting('CUSTOMIZABLE_MODELS_LIST_CREATE_PERMISSIONS')
        ]

    def get_queryset(self):
        custom_tables = TenantSpecificTable.objects.all()
        customizable_models_names = get_setting('CUSTOMIZABLE_MODELS')

        search = self.request.GET.get('search')
        if search:
            custom_tables = custom_tables.filter(name__icontains=search)
            customizable_models_names = [
                m.replace('.', get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR')).lower()
                for m in customizable_models_names
                if search in m.replace('.', get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR')).lower()
            ]

        filter_results = self.request.GET.get('filter')
        if filter_results == get_setting('CUSTOM_TABLES_FILTER_KEYWORD'):
            customizable_models_names = []
        elif filter_results == 'customizable_models':
            custom_tables = custom_tables.none()

        return {
            'custom_tables': custom_tables.order_by('name'),
            'customizable_models_names': sorted(customizable_models_names),
        }

    def get_custom_tables_names(self, custom_tables):
        return [
            get_setting('CUSTOM_TABLES_LABEL') + get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR') + t
            for t in custom_tables.values_list('name', flat=True)
        ]

    def paginate_results(self, custom_tables, customizable_models_names):
        page_number = self.request.GET.get('page')
        page_length = self.request.GET.get('length')
        total_count = len(customizable_models_names + self.get_custom_tables_names(custom_tables))

        if not page_number or not page_length:
            return [{'name': n} for n in (
                customizable_models_names + self.get_custom_tables_names(custom_tables)
            )]

        page_number = int(page_number)
        page_length = int(page_length)
        first_item_index = (page_number - 1) * page_length
        last_item_index = first_item_index + page_length
        if len(customizable_models_names) > last_item_index:
            return {
                'count': total_count,
                'results': [{'name': n} for n in (
                    customizable_models_names[first_item_index:last_item_index]
                )],
            }

        if len(customizable_models_names) >= first_item_index:
            selected_customizable_models_names = customizable_models_names[first_item_index:]
            return {
                'count': total_count,
                'results': [{'name': n} for n in (
                    selected_customizable_models_names +
                    self.get_custom_tables_names(custom_tables[
                        0:page_length - len(selected_customizable_models_names)])
                )],
            }

        return {
            'count': total_count,
            'results': [{'name': n} for n in (
                self.get_custom_tables_names(custom_tables[first_item_index:last_item_index])
            )]
        }

    def get(self, request, *args, **kwargs):
        return Response(self.paginate_results(**self.get_queryset()))

    def post(self, request, *args, **kwargs):
        serializer = TenantSpecificTableSerializer(
            data=self.request.data, context={'request': request, 'view': self})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTableDetails(generics.RetrieveUpdateDestroyAPIView):

    def get_permissions(self):
        return [
            import_from_string(permission)()
            for permission in get_setting('CUSTOMIZABLE_MODELS_RETRIEVE_UTPADE_DESTROY_PERMISSIONS')
        ]

    def get_queryset(self):
        table_slug = self.kwargs['slug']
        table_slug_parts = table_slug.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
        app = table_slug_parts[0]

        if app == get_setting('CUSTOM_TABLES_LABEL'):
            return TenantSpecificTable.objects.all()

        return ContentType.objects.filter()

    def get_object(self):
        if not hasattr(self, 'object'):
            table_slug = self.kwargs['slug']
            table_slug_parts = table_slug.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
            app = table_slug_parts[0]

            try:
                if app == get_setting('CUSTOM_TABLES_LABEL'):
                    self.object = self.get_queryset().get(name=table_slug_parts[1])
                elif (table_slug in
                        [m.replace('.', get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR')).lower()
                            for m in get_setting('CUSTOMIZABLE_MODELS')]):
                    self.object = ContentType.objects.get_by_natural_key(*table_slug_parts)
                else:
                    raise Http404()
            except ObjectDoesNotExist:
                raise Http404()
        return self.object

    def get_serializer_class(self):
        obj = self.get_object()
        if type(obj).__name__ == 'TenantSpecificTable':
            return TenantSpecificTableSerializer

        return TenantSpecificFieldsModelDefinitionsUpdateSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()

        if type(obj).__name__ == 'TenantSpecificTable':
            TenantSpecificFieldDefinition.objects.filter(
                table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                table_id=obj.id
            ).delete()
            obj.delete()
        else:
            TenantSpecificFieldDefinition.objects.filter(
                table_content_type=obj
            ).delete()

        return Response()


class TenantSpecificTableRowViewset(viewsets.ModelViewSet):
    permission_classes = [DjangoTenantSpecificTablePermissions]

    def get_queryset(self):
        table_slug = self.kwargs['slug']
        if get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR') in table_slug:
            table_slug_parts = table_slug.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
            if table_slug_parts[0] == get_setting('CUSTOM_TABLES_LABEL'):
                try:
                    return get_custom_table_manager(table_slug_parts[1]).all()
                except TenantSpecificTable.DoesNotExist:
                    pass

        raise Http404()

    def get_serializer_class(self):
        table_slug = self.kwargs['slug']
        if get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR') in table_slug:
            table_slug_parts = table_slug.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
            if table_slug_parts[0] == get_setting('CUSTOM_TABLES_LABEL'):
                try:
                    return get_tenant_specific_table_row_serializer_class(table_slug_parts[1])
                except TenantSpecificTable.DoesNotExist:
                    pass

        raise Http404()
