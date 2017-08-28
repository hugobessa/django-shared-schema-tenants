from django.db import transaction
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from shared_schema_tenants.models import Tenant
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Creates a new Tenant'

    def handle(self, *args, **options):
        name = input('Enter the Tenant name: ')
        slug = input('Enter the Tenant slug: (%s)' % slugify(name))
        domain = input('Enter the Tenant site: (localhost:8000)')

        if not slug:
            slug = slugify(name)

        if not domain:
            domain = 'localhost:8000'

        with transaction.atomic():
            tenant = Tenant.objects.create(name=name, slug=slug)
            site = Site.objects.create(name=tenant.slug, domain=domain)
            tenant.tenant_sites.create(site=site)

            self.stdout.write(self.style.SUCCESS('Successfully created Tenant %s' % name))
