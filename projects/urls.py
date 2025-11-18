# projects/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project-list'),
    path('project/new/', views.project_create, name='project-create'),
    path('project/<int:pk>/edit/', views.project_update, name='project-update'),
    path('project/<int:pk>/', views.project_detail, name='project-detail'),
    path('project/<int:pk>/request-delete/', views.project_request_deletion, name='project-request-delete'),
    path('project/<int:project_id>/import/', views.import_tasks, name='import-tasks'),

    # A meglévő tételsor URL-ek
    path('tetelsor/<int:pk>/edit_quantity/', views.tetelsor_update_quantity, name='tetelsor-edit-quantity'),
    path('tetelsor/<int:pk>/edit/', views.tetelsor_update, name='tetelsor-edit'),

    # === EZ A TELJESEN ÚJ SOR A TÉTELSOR TÖRLÉSÉHEZ (Kérés 1) ===
    path('tetelsor/<int:pk>/delete/', views.tetelsor_delete, name='tetelsor-delete'),
]