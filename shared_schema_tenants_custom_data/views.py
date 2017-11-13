from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.db import transaction
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from shared_schema_tenants_custom_data.settings import get_setting
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTable, TenantSpecificFieldDefinition)
from shared_schema_tenants_custom_data.serializers import (
    TenantSpecificFieldDefinitionCreateSerializer, TenantSpecificFieldDefinitionUpdateSerializer,
    get_tenant_specific_table_row_serializer_class)
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import get_custom_table_manager


class CustomizableModelsList(APIView):
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
            return customizable_models_names + self.get_custom_tables_names(custom_tables)

        page_number = int(page_number)
        page_length = int(page_length)
        first_item_index = (page_number - 1) * page_length
        last_item_index = first_item_index + page_length
        if len(customizable_models_names) > last_item_index:
            return {
                'count': total_count,
                'results': customizable_models_names[first_item_index:last_item_index],
            }

        if len(customizable_models_names) >= first_item_index:
            selected_customizable_models_names = customizable_models_names[first_item_index:]
            return {
                'count': total_count,
                'results': (
                    selected_customizable_models_names +
                    self.get_custom_tables_names(custom_tables[
                        0:page_length - len(selected_customizable_models_names)])
                ),
            }

        return {
            'count': total_count,
            'results': self.get_custom_tables_names(custom_tables[first_item_index:last_item_index])
        }

    def get(self, request, *args, **kwargs):
        return Response(self.paginate_results(**self.get_queryset()))


class CustomTableDetails(generics.RetrieveUpdateDestroyAPIView):

    def get_serializer_context(self):
        return {
            'request': self.request,
            'view': self,
        }

    def get_custom_table_serializer_context(self, table_name):
        context = self.get_serializer_context()
        context['table_content_type'] = ContentType.objects.get_for_model(TenantSpecificTable)
        context['table_id'] = TenantSpecificTable.objects.get(name=table_name).id
        return context

    def get_customizable_model_serializer_context(self, model_str):
        context = self.get_serializer_context()
        context['table_content_type'] = ContentType.objects.get_by_natural_key(
            *model_str.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
        )
        return context

    def retrieve(self, request, *args, **kwargs):
        table_slug = self.kwargs['slug']
        table_slug_parts = table_slug.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
        app = table_slug_parts[0]

        if app == get_setting('CUSTOM_TABLES_LABEL'):
            definitions = TenantSpecificFieldDefinition.objects.filter(
                table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                table_id=TenantSpecificTable.objects.get(name=table_slug_parts[1]).id
            )
        else:
            definitions = TenantSpecificFieldDefinition.objects.filter(
                table_content_type=ContentType.objects.get_by_natural_key(*table_slug_parts)
            )

        return Response(TenantSpecificFieldDefinitionCreateSerializer(definitions, many=True).data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.get('partial', False)

        table_slug = self.kwargs['slug']
        table_slug_parts = table_slug.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
        app = table_slug_parts[0]

        if app == get_setting('CUSTOM_TABLES_LABEL'):
            try:
                context = self.get_custom_table_serializer_context(table_slug_parts[-1])
            except TenantSpecificTable.DoesNotExist:
                new_table = TenantSpecificTable.objects.create(name=table_slug_parts[-1])
                context = {
                    'table_content_type': ContentType.objects.get_for_model(TenantSpecificTable),
                    'table_id': new_table.id,
                }

        else:
            context = self.get_customizable_model_serializer_context(table_slug)

        definitions_data = request.data
        errors = []
        has_errors = False

        if context.get('table_id'):
            definitions = TenantSpecificFieldDefinition.objects.filter(
                table_content_type=context['table_content_type'],
                table_id=context.get('table_id')
            )
        else:
            definitions = TenantSpecificFieldDefinition.objects.filter(
                table_content_type=context['table_content_type'],
            )

        definitions_data_ids = [y['id'] for y in definitions_data if y.get('id', False)]
        definitions_ids_to_be_deleted = [x.id for x in definitions if x not in definitions_data_ids]

        try:
            with transaction.atomic():
                for definition in definitions_data:
                    if definition.get('id'):
                        try:
                            old_definition = TenantSpecificFieldDefinition.objects.get(id=definition.get('id'))
                            serializer = TenantSpecificFieldDefinitionUpdateSerializer(
                                old_definition, data=definition, context=context, partial=partial)
                        except TenantSpecificFieldDefinition.DoesNotExist:
                            serializer = TenantSpecificFieldDefinitionCreateSerializer(
                                data=definition, context=context)
                    else:
                        serializer = TenantSpecificFieldDefinitionCreateSerializer(
                            data=definition, context=context)

                    if serializer.is_valid():
                        errors.append({})
                        serializer.save()
                    else:
                        errors.append(serializer.errors)
                        has_errors = True

                if has_errors:
                    raise transaction.TransactionManagementError()

        except transaction.TransactionManagementError:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            definitions.filter(id__in=definitions_ids_to_be_deleted).delete()

            if context.get('table_id'):
                definitions = TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=context['table_content_type'],
                    table_id=context.get('table_id')
                )
            else:
                definitions = TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=context['table_content_type'],
                )

            return Response(TenantSpecificFieldDefinitionCreateSerializer(definitions, many=True).data)

    def destroy(self, request, *args, **kwargs):
        table_slug = self.kwargs['slug']
        table_slug_parts = table_slug.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
        app = table_slug_parts[0]

        if app == get_setting('CUSTOM_TABLES_LABEL'):
            with transaction.atomic():
                table = TenantSpecificTable.objects.get(name=table_slug_parts[1])
                TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                    table_id=table.id
                ).delete()
                table.delete()

        else:
            TenantSpecificFieldDefinition.objects.filter(
                table_content_type=ContentType.objects.get_by_natural_key(*table_slug_parts)
            ).delete()

        return Response()


class TenantSpecificTableRowViewset(viewsets.ModelViewSet):

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
