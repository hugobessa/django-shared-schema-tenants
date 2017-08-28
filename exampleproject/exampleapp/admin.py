from django.contrib import admin

from .models import Article, Tag


admin.site.register(Article)
admin.site.register(Tag)
