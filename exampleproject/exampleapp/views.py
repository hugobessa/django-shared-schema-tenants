from rest_framework import viewsets, permissions
from .models import Article, Tag
from .serializers import ArticleSerializer, TagSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Article.tenant_objects.all()


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tag.tenant_objects.all()
