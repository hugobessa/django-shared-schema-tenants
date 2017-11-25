from django.test import TestCase
import django.utils.version
from model_mommy import mommy
from exampleproject.articles.models import Article, Tag
from shared_schema_tenants.helpers.tenants import create_tenant, set_current_tenant, clear_current_tenant
from shared_schema_tenants.exceptions import TenantNotFoundError


class SingleTenantModelManagerTests(TestCase):

    def setUp(self):
        self.tenant_1 = create_tenant(name='tenant_1', slug='tenant_1', extra_data={})
        self.tenant_2 = create_tenant(name='tenant_2', slug='tenant_2', extra_data={})

        self.articles_t1 = mommy.make(Article, tenant=self.tenant_1, _quantity=5)
        self.articles_t2 = mommy.make(Article, tenant=self.tenant_2, _quantity=3)

        set_current_tenant(self.tenant_1.slug)

        self.articles_manager = Article.objects
        if django.utils.version.get_complete_version()[1] < 10:
            self.articles_manager = Article.tenant_objects

    def test_create(self):
        user = mommy.make('auth.User')
        article = self.articles_manager.create(title="Test Article", text="Test Article Description", author=user)

        self.assertEqual(article.tenant, self.tenant_1)

    def test_create_raise_exception_if_no_tenant_set_or_passed(self):
        clear_current_tenant()
        user = mommy.make('auth.User')
        with self.assertRaises(TenantNotFoundError):
            self.articles_manager.create(title="Test Article", text="Test Article Description", author=user)

    def test_create_passing_tenant(self):
        user = mommy.make('auth.User')
        article = self.articles_manager.create(tenant=self.tenant_1, title="Test Article",
                                               text="Test Article Description", author=user)

        self.assertEqual(article.tenant, self.tenant_1)

    def test_list(self):
        self.assertEqual(self.articles_manager.count(), self.tenant_1.article_set.count())
        set_current_tenant(self.tenant_2.slug)
        self.assertEqual(self.articles_manager.count(), self.tenant_2.article_set.count())

    def test_list_passing_tenant_to_get_queryset(self):
        self.assertEqual(
            self.articles_manager.get_queryset(tenant=self.tenant_1).all().count(),
            self.tenant_1.article_set.all().count())
        self.assertEqual(
            self.articles_manager.get_queryset(tenant=self.tenant_2).all().count(),
            self.articles_manager.get_queryset(tenant=self.tenant_2).all().count(),
            self.tenant_2.article_set.all().count())

    def test_list_original_queryset(self):
        self.assertEqual(self.articles_manager.get_original_queryset().all().count(), 8)

    def test_return_nothing_if_no_tenant_set_or_passed(self):
        clear_current_tenant()
        self.assertEqual(self.articles_manager.all().count(), 0)


class MultipleTenantModelManagerTests(TestCase):

    def setUp(self):
        self.tenant_1 = create_tenant(name='tenant_1', slug='tenant_1', extra_data={})
        self.tenant_2 = create_tenant(name='tenant_2', slug='tenant_2', extra_data={})

        set_current_tenant(self.tenant_1.slug)
        self.tags_t1 = mommy.make(Tag, _quantity=5)
        self.shared_tags = mommy.make(Tag, tenants=[self.tenant_1, self.tenant_2],
                                      _quantity=7)
        set_current_tenant(self.tenant_2.slug)
        self.tags_t2 = mommy.make(Tag, _quantity=3)
        for tag in self.shared_tags:
            tag.save()

        set_current_tenant(self.tenant_1.slug)

        self.tags_manager = Tag.objects
        if django.utils.version.get_complete_version()[1] < 10:
            self.tags_manager = Tag.tenant_objects

    def test_create(self):
        tag = self.tags_manager.create(text="Test tag")
        self.assertIn(self.tenant_1, tag.tenants.all())

    def test_create_raise_exception_if_no_tenant_set_or_passed(self):
        clear_current_tenant()
        with self.assertRaises(TenantNotFoundError):
            self.tags_manager.create(text="Test tag")

    def test_list(self):
        self.assertEqual(self.tags_manager.count(), len(self.tags_t1) + len(self.shared_tags))
        set_current_tenant(self.tenant_2)
        self.assertEqual(self.tags_manager.count(), len(self.tags_t2) + len(self.shared_tags))

    def test_list_passing_tenant_to_get_queryset(self):
        self.assertEqual(
            self.tags_manager.get_queryset(tenant=self.tenant_1).all().count(),
            len(self.tags_t1) + len(self.shared_tags))
        self.assertEqual(
            self.tags_manager.get_queryset(tenant=self.tenant_2).all().count(),
            len(self.tags_t2) + len(self.shared_tags))

    def test_list_original_queryset(self):
        self.assertEqual(self.tags_manager.get_original_queryset().all().count(),
                         len(self.tags_t1) + len(self.tags_t2) + len(self.shared_tags))

    def test_return_nothing_if_no_tenant_set_or_passed(self):
        clear_current_tenant()
        self.assertEqual(self.tags_manager.all().count(), 0)
