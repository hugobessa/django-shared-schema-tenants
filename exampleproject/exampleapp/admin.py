from django.contrib import admin

from exampleapp.models import Article, Tag


admin.site.register(Article)
admin.site.register(Tag)
