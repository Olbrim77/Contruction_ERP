# projects/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # PROJEKT
    path('', views.project_list, name='project-list'),
    path('project/new/', views.project_create, name='project-create'),
    path('project/<int:pk>/edit/', views.project_update, name='project-update'),
    path('project/<int:pk>/request-delete/', views.project_request_deletion, name='project-request-delete'),
    path('project/<int:pk>/', views.project_detail, name='project-detail'),

    # TÉTELSOR
    path('tetelsor/<int:pk>/edit-quantity/', views.tetelsor_update_quantity, name='tetelsor-edit-quantity'),
    path('tetelsor/<int:pk>/edit/', views.tetelsor_update, name='tetelsor-edit'),
    path('tetelsor/<int:pk>/delete/', views.tetelsor_delete, name='tetelsor-delete'),
    path('project/<int:project_id>/import/', views.import_tasks, name='import-tasks'),

    path('project/<int:project_id>/add-master/', views.tetelsor_create_from_master_step1,
         name='tetelsor-create-master-step1'),
    path('project/<int:project_id>/add-master/step2/<int:master_id>/', views.tetelsor_create_from_master_step2,
         name='tetelsor-create-master-step2'),

    # KIADÁSOK
    path('project/<int:project_id>/expense/new/', views.expense_create, name='expense-create'),
    path('expense/<int:pk>/edit/', views.expense_update, name='expense-update'),
    path('expense/<int:pk>/delete/', views.expense_delete, name='expense-delete'),

    # NAPI JELENTÉS
    path('project/<int:project_id>/daily-log/new/', views.daily_log_create, name='daily-log-create'),
    path('daily-log/<int:pk>/edit/', views.daily_log_update, name='daily-log-update'),
    path('daily-log/<int:pk>/delete/', views.daily_log_delete, name='daily-log-delete'),

    # GANTT
    path('project/<int:project_id>/gantt/', views.gantt_view, name='gantt-view'),
    path('project/<int:project_id>/gantt/data/', views.gantt_data, name='gantt-data'),

    # KATALÓGUS (MASTER ITEM)
    path('catalog/', views.master_item_list, name='master-item-list'),
    path('catalog/new/', views.master_item_create, name='master-item-create'),
    path('catalog/<int:pk>/edit/', views.master_item_update, name='master-item-update'),
    path('catalog/<int:pk>/delete/', views.master_item_delete, name='master-item-delete'),

    # === ÚJ: RECEPTÚRA SZERKESZTŐ ===
    path('catalog/<int:pk>/components/', views.master_item_components, name='master-item-components'),
    path('catalog/component/<int:pk>/delete/', views.master_item_component_delete, name='master-item-component-delete'),
]