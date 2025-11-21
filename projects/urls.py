# projects/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # =========================================================
    # PROJEKT FŐOLDAL ÉS ALAP KEZELÉS (CRUD)
    # =========================================================

    # Projekt lista és Dashboard
    path('', views.project_list, name='project-list'),

    # Létrehozás, Szerkesztés, Törlés
    path('project/new/', views.project_create, name='project-create'),
    path('project/<int:pk>/edit/', views.project_update, name='project-update'),
    path('project/<int:pk>/request-delete/', views.project_request_deletion, name='project-request-delete'),

    # Részletező oldal
    path('project/<int:pk>/', views.project_detail, name='project-detail'),

    # =========================================================
    # KÖLTSÉGVETÉSI TÉTELSOR (TETELSOR) KEZELÉS
    # =========================================================

    # Gyors mennyiség szerkesztés
    path('tetelsor/<int:pk>/edit-quantity/', views.tetelsor_update_quantity, name='tetelsor-edit-quantity'),

    # Részletes szerkesztés (Minden mező)
    path('tetelsor/<int:pk>/edit/', views.tetelsor_update, name='tetelsor-edit'),

    # Törlés
    path('tetelsor/<int:pk>/delete/', views.tetelsor_delete, name='tetelsor-delete'),

    # Excel Importálás
    path('project/<int:project_id>/import/', views.import_tasks, name='import-tasks'),

    # =========================================================
    # KIADÁSOK (EXPENSE) CRUD
    # =========================================================

    path('project/<int:project_id>/expense/new/', views.expense_create, name='expense-create'),
    path('expense/<int:pk>/edit/', views.expense_update, name='expense-update'),
    path('expense/<int:pk>/delete/', views.expense_delete, name='expense-delete'),

    # =========================================================
    # NAPI JELENTÉS (DAILY LOG) CRUD
    # =========================================================

    path('project/<int:project_id>/daily-log/new/', views.daily_log_create, name='daily-log-create'),
    path('daily-log/<int:pk>/edit/', views.daily_log_update, name='daily-log-update'),
    path('daily-log/<int:pk>/delete/', views.daily_log_delete, name='daily-log-delete'),

    # =========================================================
    # GANTT DIAGRAM (ÜTEMEZÉS)
    # =========================================================

    # A diagram HTML oldala
    path('project/<int:project_id>/gantt/', views.gantt_view, name='gantt-view'),

    # A diagram JSON adatforrása
    path('project/<int:project_id>/gantt/data/', views.gantt_data, name='gantt-data'),

    # 1. Metódus: Létrehozás Törzsből
    path('project/<int:project_id>/add-item/', views.tetelsor_create_from_master, name='tetelsor-create-from-master'),

]