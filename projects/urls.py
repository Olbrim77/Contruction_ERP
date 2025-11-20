from django.urls import path, include
from . import views

urlpatterns = [
    # PROJEKT
    path('', views.project_list, name='project-list'),
    path('project/new/', views.project_create, name='project-create'),
    path('project/<int:pk>/edit/', views.project_update, name='project-update'),
    path('project/<int:pk>/request-delete/', views.project_request_deletion, name='project-request-delete'),
    path('project/<int:pk>/', views.project_detail, name='project-detail'),

    # TÉTELSOR
    path('tetelsor/<int:pk>/edit_quantity/', views.tetelsor_update_quantity, name='tetelsor-edit-quantity'),
    path('tetelsor/<int:pk>/edit/', views.tetelsor_update, name='tetelsor-edit'),
    path('tetelsor/<int:pk>/delete/', views.tetelsor_delete, name='tetelsor-delete'),
    path('project/<int:project_id>/import/', views.import_tasks, name='import-tasks'),

    # KIADÁSOK
    path('project/<int:project_id>/expense/new/', views.expense_create, name='expense-create'),
    path('expense/<int:pk>/edit/', views.expense_update, name='expense-update'),
    path('expense/<int:pk>/delete/', views.expense_delete, name='expense-delete'),

    # NAPI JELENTÉS
    path('project/<int:project_id>/daily-log/new/', views.daily_log_create, name='daily-log-create'),
    path('daily-log/<int:pk>/edit/', views.daily_log_update, name='daily-log-update'),
    path('daily-log/<int:pk>/delete/', views.daily_log_delete, name='daily-log-delete'),
]