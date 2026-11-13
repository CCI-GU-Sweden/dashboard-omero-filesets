from dashboard.schema_setup import SchemaSetupCommand


class Command(SchemaSetupCommand):
    help = 'Check or explicitly create the PostgreSQL OMERO collector baseline.'
    package = 'omero_filesets'
    tables = ('omero_fileset', 'storage_policy', 'group_storage_snapshot', 'collector_run')
