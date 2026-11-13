from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection, transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from accounts.models import AuditEvent, User, VerifiedOmeroGroup
from accounts.permissions import operational_access, researcher_access, is_dashboard_admin


def storage_scope(user):
    from django.utils import timezone
    if operational_access(user):
        return True, None
    if user.is_authenticated and user.is_active and user.role == User.Role.RESEARCHER:
        groups = list(VerifiedOmeroGroup.objects.filter(user=user, valid_until__gte=timezone.localdate()).values_list('group_id', flat=True))
        if groups:
            return True, groups
    return False, None


@login_required
def storage(request):
    allowed, _ = storage_scope(request.user)
    if not allowed:
        return HttpResponseForbidden('A verified OMERO group is required.')
    return render(request, 'storage.html')


@require_GET
def storage_filesets(request):
    allowed, group = storage_scope(request.user)
    if not allowed:
        return JsonResponse({'error': 'A verified OMERO group is required.'}, status=403)
    from omero_filesets.data import InvalidStorageFilters, list_filesets
    try:
        return JsonResponse(list_filesets(request.GET, allowed_group=group))
    except InvalidStorageFilters:
        return JsonResponse({'error': 'Invalid fileset filters.'}, status=400)
    except DatabaseError:
        return JsonResponse({'error': 'Storage data is currently unavailable.'}, status=503)


@require_GET
def storage_groups(request):
    allowed, group = storage_scope(request.user)
    if not allowed:
        return JsonResponse({'error': 'A verified OMERO group is required.'}, status=403)
    from omero_filesets.data import list_groups
    try:
        return JsonResponse({'groups': list_groups(group)})
    except DatabaseError:
        return JsonResponse({'error': 'Storage data is currently unavailable.'}, status=503)


@require_GET
def fileset_detail(request, fileset_id):
    import json
    allowed, group = storage_scope(request.user)
    if not allowed:
        return JsonResponse({'error': 'A verified OMERO group is required.'}, status=403)
    if not 1 <= fileset_id <= 9223372036854775807:
        return JsonResponse({'error': 'Fileset not found.'}, status=404)
    try:
        with connection.cursor() as cursor:
            cursor.execute('''SELECT first_seen_at, last_seen_at, uncontained_image_count,
                missing_since_at, missing_runs, deleted_at,
                COALESCE((SELECT jsonb_agg(entry.value ->> 'name' ORDER BY entry.ordinal)
                    FROM jsonb_array_elements(CASE WHEN jsonb_typeof(source_files) = 'array' THEN source_files ELSE '[]'::jsonb END) WITH ORDINALITY AS entry(value, ordinal)), '[]'::jsonb), locations
                FROM public.omero_fileset WHERE fileset_id = %s''' + (' AND group_id = ANY(%s)' if group is not None else ''), [fileset_id] + ([group] if group is not None else []))
            row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Fileset not found.'}, status=404)
        def array(value):
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except ValueError:
                    return []
            return value if isinstance(value, list) else []
        result = dict(zip(('first_seen_at', 'last_seen_at', 'uncontained_image_count', 'missing_since_at', 'missing_runs', 'deleted_at'), row[:6]))
        result['source_file_names'] = [name for name in array(row[6]) if isinstance(name, str)]
        keys = ('project_id', 'project_name', 'dataset_id', 'dataset_name')
        result['locations'] = [{key: location.get(key) for key in keys} for location in array(row[7]) if isinstance(location, dict)]
        return JsonResponse(result)
    except DatabaseError:
        return JsonResponse({'error': 'Fileset details are currently unavailable.'}, status=503)


@require_GET
def storage_history(request):
    allowed, group = storage_scope(request.user)
    if not allowed:
        return JsonResponse({'error': 'A verified OMERO group is required.'}, status=403)
    from omero_filesets.data import history, InvalidStorageFilters
    try:
        return JsonResponse(history(request.GET, group, is_dashboard_admin(request.user)))
    except InvalidStorageFilters:
        return JsonResponse({'error': 'Invalid history filters.'}, status=400)
    except DatabaseError:
        return JsonResponse({'error': 'Storage history is currently unavailable.'}, status=503)


@require_GET
def storage_overview(request):
    if not operational_access(request.user):
        return JsonResponse({'error': 'Staff access required.'}, status=403)
    from omero_filesets.data import snapshot_overview
    try:
        return JsonResponse(snapshot_overview(is_dashboard_admin(request.user)))
    except DatabaseError:
        return JsonResponse({'error': 'Storage summary is currently unavailable.'}, status=503)


@require_GET
def storage_overview_card(request):
    allowed, group = storage_scope(request.user)
    if not allowed:
        return JsonResponse({'error': 'A verified OMERO group is required.'}, status=403)
    from omero_filesets.data import overview_card
    try:
        return JsonResponse(overview_card(allowed_group=group, include_billable=operational_access(request.user)))
    except DatabaseError:
        return JsonResponse({'error': 'Storage summary is currently unavailable.'}, status=503)


@require_GET
def storage_admin_data(request, kind):
    if not is_dashboard_admin(request.user):
        return JsonResponse({'error': 'Administrator access required.'}, status=403)
    if kind not in ('policies', 'health'):
        return JsonResponse({'error': 'Not found.'}, status=404)
    from omero_filesets.data import admin_table
    try:
        return JsonResponse({'rows': admin_table(kind)})
    except DatabaseError:
        return JsonResponse({'error': 'Storage data is currently unavailable.'}, status=503)


@require_GET
def storage_email_draft(request, group_id):
    if not is_dashboard_admin(request.user):
        return JsonResponse({'error': 'Administrator access required.'}, status=403)
    if not 1 <= group_id <= 9223372036854775807:
        return JsonResponse({'error': 'Group not found.'}, status=404)
    from omero_filesets.data import email_draft
    try:
        result = email_draft(group_id)
        if not result:
            return JsonResponse({'error': 'No storage snapshot exists for this group.'}, status=404)
        if not result['policy_type']:
            return JsonResponse({'error': 'No storage policy applies to this snapshot.'}, status=409)
        return JsonResponse(result)
    except DatabaseError:
        return JsonResponse({'error': 'Email draft is currently unavailable.'}, status=503)


@require_POST
def create_storage_policy(request):
    import json
    import re
    from datetime import date, timedelta
    from django.utils import timezone
    if not is_dashboard_admin(request.user):
        return JsonResponse({'error': 'Administrator access required.'}, status=403)
    try:
        data = json.loads(request.body)
        group = str(data['group_id'])
        policy = data['policy_type']
        effective = date.fromisoformat(data['valid_from'])
        billing_grace = str(data['billing_grace_days'])
        grace = str(data.get('grace_days', ''))
        rate = str(data.get('rate_ore_per_gb_day', ''))
        notes = data.get('notes', '').strip()
        if (not group.isdecimal() or not 1 <= int(group) <= 9223372036854775807 or policy not in ('TEMPORARY', 'AGREEMENT', 'CORE')
            or effective < timezone.localdate() or not billing_grace.isdecimal() or int(billing_grace) > 3650 or len(notes) > 2000
            or (policy == 'TEMPORARY' and (not grace.isdecimal() or int(grace) > 36500))
            or (policy != 'CORE' and not re.fullmatch(r'\d{1,8}(?:\.\d{1,4})?', rate))):
            raise ValueError
        grace = int(grace) if policy == 'TEMPORARY' else (0 if policy == 'AGREEMENT' else None)
        rate = '0' if policy == 'CORE' else rate
    except (ValueError, KeyError, TypeError, AttributeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid policy values or effective date.'}, status=400)
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_advisory_xact_lock(%s)', [int(group)])
                cursor.execute('SELECT policy_id, group_name, valid_from, valid_until FROM public.storage_policy WHERE group_id = %s ORDER BY valid_from FOR UPDATE', [int(group)])
                rows = cursor.fetchall()
                if not rows:
                    return JsonResponse({'error': 'No policy history exists for this group.'}, status=404)
                if any(row[2] == effective for row in rows):
                    return JsonResponse({'error': 'A policy already starts on this date.'}, status=409)
                predecessor = next((row for row in reversed(rows) if row[2] < effective), None)
                successor = next((row for row in rows if row[2] > effective), None)
                if predecessor:
                    cursor.execute('UPDATE public.storage_policy SET valid_until = %s, updated_at = now() WHERE policy_id = %s', [effective - timedelta(days=1), predecessor[0]])
                cursor.execute('''INSERT INTO public.storage_policy (group_id, group_name, policy_type, grace_days, billing_grace_days, rate_ore_per_gb_day, valid_from, valid_until, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING policy_id''', [int(group), rows[-1][1], policy, grace, int(billing_grace), rate, effective, successor[2] - timedelta(days=1) if successor else None, notes or None])
                policy_id = cursor.fetchone()[0]
            AuditEvent.objects.create(actor=request.user, target=request.user, action='storage_policy_created', before={'previous_policy_id': predecessor[0] if predecessor else None, 'previous_valid_until': predecessor[3].isoformat() if predecessor and predecessor[3] else None}, after={'policy_id': policy_id, 'group_id': int(group), 'policy_type': policy, 'valid_from': effective.isoformat(), 'grace_days': grace, 'billing_grace_days': int(billing_grace), 'rate': rate, 'notes': notes})
        return JsonResponse({'policy_id': policy_id}, status=201)
    except DatabaseError:
        return JsonResponse({'error': 'Unable to save storage policy.'}, status=503)


@login_required
def billing(request):
    if not is_dashboard_admin(request.user):
        return HttpResponseForbidden('Administrator access required.')
    return render(request, 'billing.html')


@require_GET
def billing_summary(request):
    researcher = researcher_access(request.user)
    if not is_dashboard_admin(request.user) and not researcher:
        return JsonResponse({'error': 'Administrator access required.'}, status=403)
    allowed, groups = storage_scope(request.user)
    if not allowed:
        return JsonResponse({'error': 'A verified OMERO group is required.'}, status=403)
    from omero_filesets.data import InvalidStorageFilters, list_billing
    try:
        return JsonResponse(list_billing(request.GET, allowed_groups=groups))
    except InvalidStorageFilters:
        return JsonResponse({'error': 'Invalid billing date range.'}, status=400)
    except DatabaseError:
        return JsonResponse({'error': 'Billing data is currently unavailable.'}, status=503)


