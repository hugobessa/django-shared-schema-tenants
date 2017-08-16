from django.contrib.sites.models import Site
from shared_schema_tenants.settings import DEFAULT_SITE_DOMAIN


def creates_default_site(sender, instance, created, *args, **kwargs):
    if not created:
        try:
            site = Site.objects.get(domain__icontains=DEFAULT_SITE_DOMAIN,
                                    tenant_site__tenant=instance)
            if site.domain != ('%s.%s' % (instance.slug, DEFAULT_SITE_DOMAIN)):
                site.delete()
            else:
                return
        except Site.DoesNotExist:
            pass

    site = Site.objects.create(
        name=instance.slug,
        domain='%s.%s' % (instance.slug, DEFAULT_SITE_DOMAIN))
    instance.tenant_sites.create(site=site)
