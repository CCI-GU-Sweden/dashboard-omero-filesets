# Dashboard OMERO filesets

This repository contains the OMERO fileset observation Django app for the [CCI dashboard](https://github.com/CCI-GU-Sweden/Dashboard-django). It owns its routes, views, templates, static assets, data access and overview registration. It depends on the core for authentication, shared permissions, audit events and verified OMERO group memberships; it is not a standalone Django project.

The module expects existing collector-maintained PostgreSQL tables including `public.omero_fileset`, `public.group_storage_snapshot`, `public.storage_policy` and `public.collector_run`. Its views enforce staff, administrator and verified OMERO group access; data-access functions do not provide authorization on their own. Do not expose those functions directly to users. Its overview implements the core module contract and limits researcher metrics to current verified groups.

The `collector/` directory contains the existing [OMERO storage collector](https://github.com/CCI-GU-Sweden/Omero-storage-collector) from revision `46876ba2af6d424bd4f6beefeb079b8ce0e6e9c2`, including its image build files. The collector's original license is in [COLLECTOR_LICENSE](COLLECTOR_LICENSE). `deploy/collector-cronjob.example.yaml` is a suspended, dry-run example; replace the image digest, hosts and Secret references, review network/TLS and permissions, and validate it before any use. Do not run a second collector against the same data while the existing one is active. The existing deployed collector is unchanged.

## Database setup

`python manage.py setup_omero_schema` checks the baseline without creating destination tables; add `--apply` to create all four collector tables only when no baseline objects exist. Compatible existing tables are reused without changing data. Partial or mismatching objects, including conflicting table, index and sequence names, abort the transaction. Comparison includes columns, defaults, constraints, indexes, non-internal triggers and sequence settings. It is deliberately strict and can reject a compatible modified schema for manual review; it does not validate privileges, stored data, external objects or application behavior. The setup identity needs permission to create a temporary comparison schema and create objects in `public`. Run the example `deploy/schema-setup-job.example.yaml` once per release with a reviewed dashboard image and separate migration credentials, before dependent workloads. Configure runtime/collector grants separately. The full existing collector baseline includes billing columns and policy tables even when dashboard billing is disabled.

## Optional billing

Billing is enabled by default. Set `DASHBOARD_OMERO_BILLING_ENABLED=0` on the dashboard process to disable it independently of fileset observation; restart all web processes after changing it. Billing pages, API, charge metrics, storage-policy management and billing-related email drafts are unavailable. Fileset inventory, total-storage history and ranking, group-scoped access and collector health remain available. The disabled paths use only total-storage columns and do not require billing columns or policy tables. The collector is a separate process with its own configuration and schema requirements: this switch does not disable collector billing calculations, modify the collector or erase existing data.

Code extracted from Dashboard-django retains the copyright notice in [CORE_LICENSE](CORE_LICENSE); this repository is MIT licensed.

Run frontend tests from this checkout with `node --test tests/*.test.js`; integration and authorization tests run in the dashboard core.
