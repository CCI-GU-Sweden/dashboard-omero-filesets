# Dashboard OMERO filesets

This repository is the beginning of the OMERO fileset observation module for the [CCI dashboard](https://github.com/CCI-GU-Sweden/Dashboard-django). It currently contains the PostgreSQL data-access functions extracted from the core. It is not yet a standalone Django app: routes, views, user/group authorization, templates, billing controls and overview registration still live in the core.

The module expects existing collector-maintained PostgreSQL tables including `public.omero_fileset`, `public.group_storage_snapshot`, `public.storage_policy` and `public.collector_run`. The core currently enforces staff, administrator and verified OMERO group access before calling these functions; the functions do not provide authorization on their own. Do not expose them directly to users.

The [OMERO storage collector](https://github.com/CCI-GU-Sweden/Omero-storage-collector) currently supplies the fileset data, schema and Kubernetes/OpenShift collector manifests. These have not yet been migrated here. Existing installations and database objects must be preserved during that migration. Billing and storage-policy queries remain included for now; independently enabling or disabling billing is future work.

Code extracted from Dashboard-django retains the copyright notice in [CORE_LICENSE](CORE_LICENSE); this repository is MIT licensed.
