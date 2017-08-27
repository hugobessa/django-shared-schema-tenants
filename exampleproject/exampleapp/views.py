from rest_framework import viewsets
from exampleapp.models import Article
from exampleapp.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        return Article.objects.all()
