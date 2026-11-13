"""OMERO registration and scoped overview for the core module contract."""
from django.core.exceptions import PermissionDenied

from accounts.models import User
from accounts.permissions import operational_access
from dashboard.modules import DashboardModule
from . import data
from .views import storage_scope


def can_view(user):
    # An unverified researcher can see the card's access explanation, not data.
    return user.role in (User.Role.STAFF, User.Role.ADMIN, User.Role.RESEARCHER)


def overview_metrics(user):
    allowed, groups = storage_scope(user)
    if not allowed:
        raise PermissionDenied
    summary = data.overview_card(allowed_group=groups, include_billable=operational_access(user))
    snapshot = summary['snapshot_date']
    if not snapshot:
        return [{'key': 'status', 'label': 'Status', 'value': 'No storage snapshots are available.'}]
    entries = [('filesets', 'Filesets', 0, ''), ('storage_gb', 'Total storage', 2, ' GB')]
    if operational_access(user):
        entries.append(('daily_sek', 'Billable', 2, ' SEK/day'))
    metrics = [{'key': 'status', 'label': 'Status', 'value': f'Snapshot: {snapshot}'}]
    for key, label, precision, unit in entries:
        item = summary['metrics'][key]
        value = item['value']
        display = '—' if value is None else f'{value:,.{precision}f}{unit}'
        change, comparison = item['change_percent'], summary['comparison_date']
        detail = f'{change:+.1f}% vs {comparison}' if change is not None and comparison else 'No 30-day comparison'
        metrics.append({'key': key, 'label': label, 'value': display, 'detail': detail})
    return metrics


module = DashboardModule(
    key='omero', name='OMERO Storage', eyebrow='Managed repository', icon='▣',
    url_name='storage', urlconf='omero_filesets.urls', can_view=can_view,
    get_metrics=overview_metrics, overview_template='storage_overview_card.html',
    overview_script='js/storage_overview.js',
)
