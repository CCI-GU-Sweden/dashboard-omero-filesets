# Dashboard OMERO filesets

This repository contains the OMERO fileset observation Django app for the [CCI dashboard](https://github.com/CCI-GU-Sweden/Dashboard-django). It owns its routes, views, templates, static assets, data access and overview registration. It depends on the core for authentication, shared permissions, audit events and verified OMERO group memberships; it is not a standalone Django project.

The module expects existing collector-maintained PostgreSQL tables including `public.omero_fileset`, `public.group_storage_snapshot`, `public.storage_policy` and `public.collector_run`. Its views enforce staff, administrator and verified OMERO group access; data-access functions do not provide authorization on their own. Do not expose those functions directly to users. Its overview implements the core module contract and limits researcher metrics to current verified groups.

The [OMERO storage collector](https://github.com/CCI-GU-Sweden/Omero-storage-collector) currently supplies the fileset data, schema and Kubernetes/OpenShift collector manifests. These have not yet been migrated here. Existing installations and database objects must be preserved during that migration. Billing and storage-policy queries remain included for now; independently enabling or disabling billing is future work.

Code extracted from Dashboard-django retains the copyright notice in [CORE_LICENSE](CORE_LICENSE); this repository is MIT licensed.

Run frontend tests from this checkout with `node --test tests/*.test.js`; integration and authorization tests run in the dashboard core.
