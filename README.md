# Dashboard OMERO filesets

This repository contains the OMERO fileset observation Django app for the [CCI dashboard](https://github.com/CCI-GU-Sweden/Dashboard-django). It owns its routes, views, templates, static assets, data access and overview registration. It depends on the core for authentication, shared permissions, audit events and verified OMERO group memberships; it is not a standalone Django project.

The module expects existing collector-maintained PostgreSQL tables including `public.omero_fileset`, `public.group_storage_snapshot`, `public.storage_policy` and `public.collector_run`. Its views enforce staff, administrator and verified OMERO group access; data-access functions do not provide authorization on their own. Do not expose those functions directly to users. Its overview implements the core module contract and limits researcher metrics to current verified groups.

The [OMERO storage collector](https://github.com/CCI-GU-Sweden/Omero-storage-collector) currently supplies the fileset data, schema and Kubernetes/OpenShift collector manifests. These have not yet been migrated here. Existing installations and database objects must be preserved during that migration.

## Optional billing

Billing is enabled by default. Set `DASHBOARD_OMERO_BILLING_ENABLED=0` on the dashboard process to disable it independently of fileset observation; restart all web processes after changing it. Billing pages, API, charge metrics, storage-policy management and billing-related email drafts are unavailable. Fileset inventory, total-storage history and ranking, group-scoped access and collector health remain available. The disabled paths use only total-storage columns and do not require billing columns or policy tables. The collector is a separate process with its own configuration and schema requirements: this switch does not disable collector billing calculations, modify the collector or erase existing data.

Code extracted from Dashboard-django retains the copyright notice in [CORE_LICENSE](CORE_LICENSE); this repository is MIT licensed.

Run frontend tests from this checkout with `node --test tests/*.test.js`; integration and authorization tests run in the dashboard core.
