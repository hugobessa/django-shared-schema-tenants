from django.test import TestCase
from model_mommy import mommy
from exampleproject.exampleapp.models import Article
from shared_schema_tenants.helpers.tenants import create_tenant, set_current_tenant


class SingleTenantModelManagerTests(TestCase):

    def setUp(self):
        self.tenant_1 = create_tenant(name='tenant_1', slug='tenant_1', extra_data={})
        self.tenant_2 = create_tenant(name='tenant_2', slug='tenant_2', extra_data={})

        self.articles_t1 = mommy.make(Article, tenant=self.tenant_1, _quantity=5)
        self.articles_t2 = mommy.make(Article, tenant=self.tenant_2, _quantity=3)

        set_current_tenant(self.tenant_1)

    def test_create(self):
        user = mommy.make('auth.User')
        article = Article.tenant_objects.create(title="Test Article", text="Test Article Description", author=user)

        self.assertEqual(article.tenant, self.tenant_1)

    def test_list(self):
        self.assertEqual(Article.tenant_objects.count(), self.tenant_1.article_set.count())
        set_current_tenant(self.tenant_2)
        self.assertEqual(Article.tenant_objects.count(), self.tenant_2.article_set.count())

    def test_list_passing_tenant_to_get_queryset(self):
        self.assertEqual(
            Article.tenant_objects.get_queryset(tenant=self.tenant_1).all().count(),
            self.tenant_1.article_set.all().count())
        self.assertEqual(
            Article.tenant_objects.get_queryset(tenant=self.tenant_2).all().count(),
            self.tenant_2.article_set.all().count())

    def test_list_original_queryset(self):
        self.assertEqual(Article.tenant_objects.get_original_queryset().all().count(), 8)
