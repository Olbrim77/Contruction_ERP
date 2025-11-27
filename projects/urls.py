# projects/urls.py
from django.urls import path
from . import views
from . import views_mobile  # <-- ÚJ IMPORT!

urlpatterns = [
    # --- ASZTALI NÉZETEK (VÁLTOZATLAN) ---
    path('', views.project_list, name='project-list'),
    path('project/new/', views.project_create, name='project-create'),
    path('project/<int:pk>/edit/', views.project_update, name='project-update'),
    path('project/<int:pk>/request-delete/', views.project_request_deletion, name='project-request-delete'),
    path('project/<int:pk>/', views.project_detail, name='project-detail'),

    path('tetelsor/<int:pk>/edit-quantity/', views.tetelsor_update_quantity, name='tetelsor-edit-quantity'),
    path('tetelsor/<int:pk>/edit/', views.tetelsor_update, name='tetelsor-edit'),
    path('tetelsor/<int:pk>/delete/', views.tetelsor_delete, name='tetelsor-delete'),
    path('project/<int:project_id>/import/', views.import_tasks, name='import-tasks'),

    path('project/<int:project_id>/add-master/', views.tetelsor_create_from_master_step1,
         name='tetelsor-create-master-step1'),
    path('project/<int:project_id>/add-master/step2/<int:master_id>/', views.tetelsor_create_from_master_step2,
         name='tetelsor-create-master-step2'),

    path('project/<int:project_id>/expense/new/', views.expense_create, name='expense-create'),
    path('expense/<int:pk>/edit/', views.expense_update, name='expense-update'),
    path('expense/<int:pk>/delete/', views.expense_delete, name='expense-delete'),

    path('project/<int:project_id>/daily-log/new/', views.daily_log_create, name='daily-log-create'),
    path('daily-log/<int:pk>/edit/', views.daily_log_update, name='daily-log-update'),
    path('daily-log/<int:pk>/delete/', views.daily_log_delete, name='daily-log-delete'),

    path('project/<int:project_id>/gantt/', views.gantt_view, name='gantt-view'),
    path('project/<int:project_id>/gantt/data/', views.gantt_data, name='gantt-data'),

    path('project/<int:pk>/quote-print/', views.project_quote_html, name='project-quote-html'),
    path('project/<int:pk>/pdf-quote/', views.project_quote_pdf, name='project-quote-pdf'),
    path('project/<int:pk>/status/<str:status_code>/', views.project_status_update, name='project-status-update'),

    path('catalog/', views.master_item_list, name='master-item-list'),
    path('catalog/new/', views.master_item_create, name='master-item-create'),
    path('catalog/import/', views.import_master_items, name='master-item-import'),
    path('catalog/<int:pk>/edit/', views.master_item_update, name='master-item-update'),
    path('catalog/<int:pk>/delete/', views.master_item_delete, name='master-item-delete'),
    path('catalog/<int:pk>/components/', views.master_item_components, name='master-item-components'),
    path('catalog/component/<int:pk>/delete/', views.master_item_component_delete, name='master-item-component-delete'),

    path('project/<int:project_id>/document/new/', views.document_create, name='document-create'),
    path('document/<int:pk>/delete/', views.document_delete, name='document-delete'),

    path('project/<int:project_id>/order/new/', views.material_order_create, name='material-order-create'),
    path('project/<int:project_id>/order/from-budget/', views.material_order_create_from_budget,
         name='material-order-from-budget'),
    path('order/<int:pk>/edit/', views.material_order_update, name='material-order-update'),
    path('order/<int:pk>/delete/', views.material_order_delete, name='material-order-delete'),
    path('order/<int:pk>/print/', views.material_order_print, name='material-order-print'),
    path('order/<int:pk>/finalize/', views.material_order_finalize, name='material-order-finalize'),

    # === MOBIL NÉZETEK (TEREPNAPLÓ) ===
    path('mobile/', views_mobile.mobile_dashboard, name='mobile-dashboard'),
    path('mobile/project/<int:pk>/', views_mobile.mobile_project_detail, name='mobile-project-detail'),
    path('mobile/project/<int:project_id>/log/', views_mobile.mobile_daily_log, name='mobile-daily-log'),
    path('task/<int:pk>/complete/', views.task_complete, name='task-complete'),
    path('task/<int:pk>/complete/', views.task_complete, name='task-complete'),
    path('project/<int:project_id>/gantt/', views.gantt_view, name='gantt-view'),
    path('project/<int:project_id>/gantt/data/', views.gantt_data, name='gantt-data'),
    path('project/<int:project_id>/gantt/update/', views.gantt_update, name='gantt-update'), # <-- ÚJ
    path('tetelsor/<int:pk>/sync-to-master/', views.sync_tetelsor_to_master, name='sync-tetelsor-to-master'),
    path('global-gantt/', views.global_gantt_view, name='global-gantt'),
    path('global-gantt/data/', views.global_gantt_data, name='global-gantt-data'),
    path('global-gantt/update/', views.global_gantt_update, name='global-gantt-update'),
]