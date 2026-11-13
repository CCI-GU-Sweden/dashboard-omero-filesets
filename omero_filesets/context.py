from django.conf import settings


def billing_enabled():
    return getattr(settings, 'DASHBOARD_OMERO_BILLING_ENABLED', True)


def billing_context(request):
    return {'omero_billing_enabled': billing_enabled()}
