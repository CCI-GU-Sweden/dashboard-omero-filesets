from django.urls import path
from . import views

urlpatterns = [
    path('storage/', views.storage, name='storage'),
    path('storage/billing/', views.billing, name='billing'),
    path('api/omero/billing', views.billing_summary, name='billing_summary'),
    path('api/omero/filesets', views.storage_filesets, name='storage_filesets'),
    path('api/omero/filesets/<int:fileset_id>', views.fileset_detail, name='fileset_detail'),
    path('api/omero/groups', views.storage_groups, name='storage_groups'),
    path('api/omero/groups/<int:group_id>/email-draft', views.storage_email_draft, name='storage_email_draft'),
    path('api/omero/history', views.storage_history, name='storage_history'),
    path('api/omero/overview', views.storage_overview, name='storage_overview'),
    path('api/omero/overview-card', views.storage_overview_card, name='storage_overview_card'),
    path('api/omero/policies', views.create_storage_policy, name='create_storage_policy'),
    path('api/omero/admin/<str:kind>', views.storage_admin_data, name='storage_admin_data'),
]
