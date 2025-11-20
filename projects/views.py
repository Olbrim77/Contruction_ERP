# projects/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog, Supplier, Material
from .forms import ProjectForm, TetelsorQuantityForm, TetelsorEditForm, ExpenseForm, DailyLogForm
from django.db.models import Sum, F
from decimal import Decimal
from django.utils import timezone
import math
from datetime import timedelta
import openpyxl
from django.core.files.storage import default_storage
import os
from django.conf import settings

# --- SEGÉDFÜGGVÉNYEK ---
def calculate_work_end_date(start_date, workdays):
    if not start_date or workdays == 0: return None
    current_date = start_date
    days_to_add = int(workdays)
    while current_date.weekday() >= 5: current_date += timedelta(days=1)
    added_days = 0
    while added_days < days_to_add:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5: added_days += 1
    return current_date

def get_cell_value(row, index, default=""):
    try: val = row[index].value; return str(val) if val is not None else default
    except (IndexError, AttributeError): return default

def get_cell_decimal(row, index):
    try: val = row[index].value
    except (IndexError, AttributeError): return Decimal(0)
    try: return Decimal(val) if val is not None else Decimal(0)
    except (TypeError, ValueError): return Decimal(0)

# --- FŐ NÉZETEK ---
def project_list(request):
    projects = Project.objects.exclude(status='TORLES_KERELEM').order_by('start_date')
    context = {'projects_key': projects}
    return render(request, 'projects/project_list.html', context)

def project_detail(request, pk):
    project = get_object_or_404(Project, id=pk)
    tasks = project.tetelsorok.all().order_by('sorszam')
    expenses = project.expenses.all().order_by('-date')
    summary_plan = tasks.aggregate(
        plan_anyag=Sum('anyag_osszesen'), plan_dij_sajat=Sum('sajat_munkadij_osszesen'),
        plan_dij_alv=Sum('alv_munkadij_osszesen'), plan_hours=Sum(F('mennyiseg') * F('normaido'))
    )
    plan_anyag = summary_plan.get('plan_anyag') or Decimal(0)
    plan_dij_sajat = summary_plan.get('plan_dij_sajat') or Decimal(0)
    plan_dij_alv = summary_plan.get('plan_dij_alv') or Decimal(0)
    plan_dij = plan_dij_sajat + plan_dij_alv
    plan_total = plan_anyag + plan_dij
    actual_anyag = expenses.filter(category='ANYAG').aggregate(Sum('amount_netto'))['amount_netto__sum'] or Decimal(0)
    actual_dij = expenses.filter(category='MUNKADIJ').aggregate(Sum('amount_netto'))['amount_netto__sum'] or Decimal(0)
    actual_egyeb = expenses.filter(category='EGYEB').aggregate(Sum('amount_netto'))['amount_netto__sum'] or Decimal(0)
    actual_total = actual_anyag + actual_dij + actual_egyeb
    balance = plan_total - actual_total
    vat_rate = project.vat_rate
    total_vat = (plan_total * vat_rate) / Decimal(100)
    total_project_brutto = plan_total + total_vat
    total_effort_hours = summary_plan.get('plan_hours') or Decimal(0)
    hours_per_day = project.hours_per_day
    total_workdays = 0
    if hours_per_day and hours_per_day > 0:
        total_workdays = math.ceil(total_effort_hours / hours_per_day)
    calculated_end_date = calculate_work_end_date(project.start_date, total_workdays)

    context = {
        'project': project, 'tasks': tasks, 'expenses': expenses,
        'plan_anyag': plan_anyag, 'plan_dij': plan_dij, 'plan_dij_sajat': plan_dij_sajat, 'plan_dij_alv': plan_dij_alv,
        'plan_total': plan_total, 'actual_anyag': actual_anyag, 'actual_dij': actual_dij, 'actual_total': actual_total,
        'balance': balance, 'vat_rate': vat_rate, 'total_vat': total_vat,
        'total_project_brutto': total_project_brutto, 'total_effort_hours': total_effort_hours,
        'total_workdays': total_workdays, 'calculated_end_date': calculated_end_date
    }
    return render(request, 'projects/project_detail.html', context)

# --- PROJEKT CRUD ---
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid(): new_project = form.save(); return redirect('project-detail', pk=new_project.id)
    else: form = ProjectForm()
    context = {'form': form}; return render(request, 'projects/project_form.html', context)

def project_update(request, pk):
    project_to_edit = get_object_or_404(Project, id=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project_to_edit)
        if form.is_valid():
            recalculate_dij = False
            if 'hourly_rate' in form.changed_data: recalculate_dij = True; new_rate = form.cleaned_data['hourly_rate']
            form.save()
            if recalculate_dij:
                project_to_edit.tetelsorok.update(dij_egysegre_sajat = new_rate * F('normaido'))
                project_to_edit.tetelsorok.update(dij_egysegre_alv = Decimal(0))
                project_to_edit.tetelsorok.update(sajat_munkadij_osszesen = F('mennyiseg') * F('dij_egysegre_sajat'))
                project_to_edit.tetelsorok.update(alv_munkadij_osszesen = F('mennyiseg') * F('dij_egysegre_alv'))
            return redirect('project-detail', pk=project_to_edit.id)
    else: form = ProjectForm(instance=project_to_edit)
    context = {'form': form, 'project': project_to_edit}; return render(request, 'projects/project_form.html', context)

def project_request_deletion(request, pk):
    project_to_delete = get_object_or_404(Project, id=pk)
    if request.method == 'POST': project_to_delete.status = 'TORLES_KERELEM'; project_to_delete.save(); return redirect('project-list')
    context = {'project': project_to_delete}; return render(request, 'projects/project_confirm_delete.html', context)

# --- IMPORT ---
def import_tasks(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST' and 'temp_file_path' in request.POST:
        temp_file_path = request.POST.get('temp_file_path'); selected_sheets = request.POST.getlist('sheets'); full_path = os.path.join(settings.MEDIA_ROOT, temp_file_path); row_counter = 1
        try:
            workbook = openpyxl.load_workbook(full_path, data_only=True)
            for sheet_name in selected_sheets:
                if sheet_name not in workbook.sheetnames: continue
                ws = workbook[sheet_name]
                for row in ws.iter_rows(min_row=2):
                    if not row or len(row) < 2: continue
                    tetelszam = get_cell_value(row, 1);
                    if not tetelszam: continue
                    leiras = get_cell_value(row, 2); mennyiseg = get_cell_decimal(row, 3); egyseg = get_cell_value(row, 4); material_name = get_cell_value(row, 5)
                    megjegyzes = get_cell_value(row, 9); engy_kod = get_cell_value(row, 10); k_jelzo = get_cell_value(row, 11); normaido = get_cell_decimal(row, 13)
                    cpr_kod = get_cell_value(row, 15)
                    munkanem_obj, _ = Munkanem.objects.get_or_create(nev=get_cell_value(row, 12).strip()) if get_cell_value(row, 12) else (None, False)
                    alvallalkozo_obj, _ = Alvallalkozo.objects.get_or_create(nev=get_cell_value(row, 14).strip()) if get_cell_value(row, 14) else (None, False)
                    material_obj = None
                    if material_name:
                         material_obj, created = Material.objects.get_or_create(name=material_name.strip(), defaults={'unit': get_cell_value(row, 4), 'price': Decimal(0)} )
                    defaults_data = {
                        'sorszam': str(row_counter), 'leiras': leiras, 'mennyiseg': mennyiseg, 'egyseg': egyseg, 'material': material_obj,
                        'megjegyzes': megjegyzes, 'engy_kod': engy_kod, 'k_jelzo': k_jelzo, 'normaido': normaido, 'cpr_kod': cpr_kod,
                        'munkanem': munkanem_obj, 'alvallalkozo': alvallalkozo_obj,
                    }
                    Tetelsor.objects.update_or_create(project=project, tetelszam=tetelszam, defaults=defaults_data)
                    row_counter += 1
            workbook.close()
        except Exception as e: print(f"Hiba: {e}")
        finally:
            if default_storage.exists(temp_file_path): default_storage.delete(temp_file_path)
        return redirect('project-detail', pk=project.id)
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file'];
        if not excel_file.name.endswith('.xlsx'): return redirect('project-detail', pk=project.id)
        temp_file_name = f"temp/{project.id}_{excel_file.name}"; temp_file_path = default_storage.save(temp_file_name, excel_file)
        full_path = os.path.join(settings.MEDIA_ROOT, temp_file_path)
        try:
            workbook = openpyxl.load_workbook(full_path, read_only=True, data_only=True)
            sheet_names = workbook.sheetnames; workbook.close()
            context = {'project': project, 'sheet_names': sheet_names, 'temp_file_path': temp_file_path}
            return render(request, 'projects/import_step2_select.html', context)
        except Exception as e:
            if default_storage.exists(temp_file_path): default_storage.delete(temp_file_path)
            print(f"Hiba az Excel olvasásakor: {e}"); return redirect('project-detail', pk=project.id)
    context = {'project': project}; return render(request, 'projects/import_step1_upload.html', context)

# --- TETELSOR CRUD ---
def tetelsor_update_quantity(request, pk):
    tetelsor = get_object_or_404(Tetelsor, id=pk)
    if request.method == 'POST':
        form = TetelsorQuantityForm(request.POST, instance=tetelsor);
        if form.is_valid(): form.save(); return redirect('project-detail', pk=tetelsor.project.id)
    else: form = TetelsorQuantityForm(instance=tetelsor)
    context = {'form': form, 'tetelsor': tetelsor}; return render(request, 'projects/tetelsor_form.html', context)

def tetelsor_update(request, pk):
    tetelsor = get_object_or_404(Tetelsor, id=pk)
    if request.method == 'POST':
        form = TetelsorEditForm(request.POST, instance=tetelsor);
        if form.is_valid(): form.save(); return redirect('project-detail', pk=tetelsor.project.id)
    else: form = TetelsorEditForm(instance=tetelsor)
    context = {'form': form, 'tetelsor': tetelsor}; return render(request, 'projects/tetelsor_edit_form.html', context)

def tetelsor_delete(request, pk):
    tetelsor = get_object_or_404(Tetelsor, id=pk)
    project_id = tetelsor.project.id
    if request.method == 'POST': tetelsor.delete(); return redirect('project-detail', pk=project_id)
    context = {'tetelsor': tetelsor}; return render(request, 'projects/tetelsor_confirm_delete.html', context)

# --- KIADÁS CRUD ---
def expense_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES);
        if form.is_valid():
            expense = form.save(commit=False); expense.project = project; expense.save()
            return redirect('project-detail', pk=project.id)
    else: form = ExpenseForm()
    context = {'form': form, 'project': project}; return render(request, 'projects/expense_form.html', context)

def expense_update(request, pk):
    expense = get_object_or_404(Expense, id=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid(): form.save(); return redirect('project-detail', pk=expense.project.id)
    else: form = ExpenseForm(instance=expense)
    context = {'form': form, 'expense': expense}; return render(request, 'projects/expense_form.html', context)

def expense_delete(request, pk):
    expense = get_object_or_404(Expense, id=pk)
    project_id = expense.project.id
    if request.method == 'POST': expense.delete(); return redirect('project-detail', pk=project_id)
    context = {'expense': expense}; return render(request, 'projects/expense_confirm_delete.html', context)

# --- NAPLÓ CRUD ---
def daily_log_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = DailyLogForm(request.POST);
        if form.is_valid():
            log_entry = form.save(commit=False); log_entry.project = project; log_entry.save()
            return redirect('project-detail', pk=project.id)
    else:
        try:
            existing_log = DailyLog.objects.get(project=project, date=timezone.localdate())
            form = DailyLogForm(instance=existing_log)
        except DailyLog.DoesNotExist: form = DailyLogForm(initial={'date': timezone.localdate()})
        except Exception: form = DailyLogForm()
    context = {'form': form, 'project': project}; return render(request, 'projects/daily_log_form.html', context)

def daily_log_update(request, pk):
    log_entry = get_object_or_404(DailyLog, id=pk)
    if request.method == 'POST':
        form = DailyLogForm(request.POST, instance=log_entry)
        if form.is_valid(): form.save(); return redirect('project-detail', pk=log_entry.project.id)
    else: form = DailyLogForm(instance=log_entry)
    context = {'form': form, 'log_entry': log_entry}; return render(request, 'projects/daily_log_form.html', context)

def daily_log_delete(request, pk):
    log_entry = get_object_or_404(DailyLog, id=pk)
    project_id = log_entry.project.id
    if request.method == 'POST': log_entry.delete(); return redirect('project-detail', pk=project_id)
    context = {'log_entry': log_entry}; return render(request, 'projects/daily_log_confirm_delete.html', context)