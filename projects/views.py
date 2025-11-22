# projects/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog, Supplier, Material, MasterItem, \
    ItemComponent
# === JAVÍTOTT IMPORT SOR (ItemComponentForm HOZZÁADVA) ===
from .forms import (
    ProjectForm, TetelsorQuantityForm, TetelsorEditForm, ExpenseForm,
    DailyLogForm, TetelsorCreateFromMasterForm, MasterItemForm, ItemComponentForm
)

from django.db.models import Sum, F, Q
from decimal import Decimal
from django.utils import timezone
import math
from datetime import timedelta
import openpyxl
from django.core.files.storage import default_storage
import os
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse


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
    try:
        val = row[index].value; return str(val).strip() if val is not None else default
    except (IndexError, AttributeError):
        return default


def get_cell_decimal(row, index):
    try:
        val = row[index].value
        if isinstance(val, str) or isinstance(val, (int, float, Decimal)):
            return Decimal(val) if val is not None else Decimal(0)
        val_str = str(val).replace("\xa0", "").replace(" ", "").replace("Ft", "").replace(",", ".")
        if not val_str: return Decimal(0)
        return Decimal(val_str)
    except (TypeError, ValueError, IndexError, AttributeError):
        return Decimal(0)


def get_next_version_id(base_id):
    counter = 1
    while True:
        new_id = f"{base_id}-E_{counter:03d}"
        if not MasterItem.objects.filter(tetelszam=new_id).exists():
            return new_id
        counter += 1


# --- FŐ NÉZETEK ---

def project_list(request):
    projects = Project.objects.exclude(status='TORLES_KERELEM').order_by('start_date')
    search_query = request.GET.get('q')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(client__icontains=search_query)
        )
    all_budgets = Tetelsor.objects.filter(project__in=projects).aggregate(
        mat=Sum('anyag_osszesen'), lab_sajat=Sum('sajat_munkadij_osszesen'), lab_alv=Sum('alv_munkadij_osszesen')
    )
    global_plan = (all_budgets['mat'] or 0) + (all_budgets['lab_sajat'] or 0) + (all_budgets['lab_alv'] or 0)
    global_spent = Expense.objects.filter(project__in=projects).aggregate(Sum('amount_netto'))['amount_netto__sum'] or 0
    global_balance = global_plan - global_spent
    status_counts = {
        'TERVEZES': projects.filter(status='TERVEZES').count(),
        'FOLYAMATBAN': projects.filter(status='FOLYAMATBAN').count(),
        'BEFEJEZETT': projects.filter(status='BEFEJEZETT').count(),
        'LEZART': projects.filter(status='LEZART').count(),
    }
    context = {'projects_key': projects, 'global_plan': global_plan, 'global_spent': global_spent,
               'global_balance': global_balance, 'status_counts': status_counts, 'search_query': search_query or ""}
    return render(request, 'projects/project_list.html', context)


def project_detail(request, pk):
    project = get_object_or_404(Project, id=pk)
    tasks = project.tetelsorok.all().order_by('sorszam')
    expenses = project.expenses.all().order_by('-date')
    expense_filter = request.GET.get('expense_category_filter')
    if expense_filter: expenses = expenses.filter(category=expense_filter)
    munkanem_filter = request.GET.get('munkanem_filter')
    if munkanem_filter: tasks = tasks.filter(master_item__munkanem__nev=munkanem_filter)

    munkanem_list = Munkanem.objects.all().order_by('nev')
    expense_category_list = Expense.CATEGORY_CHOICES

    summary_plan = tasks.aggregate(
        plan_anyag=Sum('anyag_osszesen'),
        plan_dij_sajat=Sum('sajat_munkadij_osszesen'),
        plan_dij_alv=Sum('alv_munkadij_osszesen'),
        plan_hours=Sum(F('mennyiseg') * F('master_item__normaido'))
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
        'total_workdays': total_workdays, 'calculated_end_date': calculated_end_date,
        'munkanem_list': munkanem_list, 'expense_category_list': expense_category_list,
        'current_munkanem': munkanem_filter, 'current_expense_category': expense_filter
    }
    return render(request, 'projects/project_detail.html', context)


# --- GANTT ---
def gantt_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, 'projects/gantt_view.html', {'project': project})


def gantt_data(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = project.tetelsorok.all().order_by('sorszam')
    data = []
    for task in tasks:
        start = project.start_date or timezone.now().date()
        norma = task.master_item.normaido or Decimal(0);
        mennyiseg = task.mennyiseg or Decimal(0)
        hours_per_day = project.hours_per_day or Decimal(8)
        total_hours = mennyiseg * norma
        duration = 1
        if total_hours > 0: duration = math.ceil(total_hours / hours_per_day)
        data.append({
            'id': task.id, 'text': f"{task.master_item.tetelszam} - {task.master_item.leiras[:30]}...",
            'start_date': start.strftime("%Y-%m-%d"), 'duration': duration,
            'progress': float(task.progress_percentage) / 100, 'open': True,
            'mennyiseg': f"{task.mennyiseg} {task.egyseg}",
            'munkanem': task.master_item.munkanem.nev if task.master_item.munkanem else "-"
        })
    return JsonResponse({"data": data})


# --- PROJEKT CRUD ---
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid(): new_project = form.save(); return redirect('project-detail', pk=new_project.id)
    else:
        form = ProjectForm()
    context = {'form': form}
    return render(request, 'projects/project_form.html', context)


def project_update(request, pk):
    project_to_edit = get_object_or_404(Project, id=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project_to_edit)
        if form.is_valid():
            recalculate_dij = False
            if 'hourly_rate' in form.changed_data: recalculate_dij = True
            form.save()
            if recalculate_dij:
                for tetel in project_to_edit.tetelsorok.all(): tetel.save()
            return redirect('project-detail', pk=project_to_edit.id)
    else:
        form = ProjectForm(instance=project_to_edit)
    context = {'form': form, 'project': project_to_edit};
    return render(request, 'projects/project_form.html', context)


def project_request_deletion(request, pk):
    project_to_delete = get_object_or_404(Project, id=pk)
    if request.method == 'POST': project_to_delete.status = 'TORLES_KERELEM'; project_to_delete.save(); return redirect(
        'project-list')
    context = {'project': project_to_delete};
    return render(request, 'projects/project_confirm_delete.html', context)


# --- IMPORT LOGIKA ---
def import_tasks(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST' and 'temp_file_path' in request.POST:
        temp_file_path = request.POST.get('temp_file_path');
        selected_sheets = request.POST.getlist('sheets');
        full_path = os.path.join(settings.MEDIA_ROOT, temp_file_path);
        row_counter = 1
        try:
            workbook = openpyxl.load_workbook(full_path, data_only=True)
            for sheet_name in selected_sheets:
                if sheet_name not in workbook.sheetnames: continue
                ws = workbook[sheet_name]
                for row in ws.iter_rows(min_row=2):
                    if not row or len(row) < 2: continue
                    tetelszam_raw = get_cell_value(row, 1);
                    if not tetelszam_raw: continue
                    leiras_raw = get_cell_value(row, 2);
                    mennyiseg = get_cell_decimal(row, 3);
                    egyseg = get_cell_value(row, 4);
                    import_ar = get_cell_decimal(row, 5)
                    megjegyzes = get_cell_value(row, 9);
                    engy_kod = get_cell_value(row, 10);
                    k_jelzo = get_cell_value(row, 11);
                    normaido = get_cell_decimal(row, 13)
                    cpr_kod = get_cell_value(row, 15)
                    munkanem_obj, _ = Munkanem.objects.get_or_create(
                        nev=get_cell_value(row, 12).strip()) if get_cell_value(row, 12) else (None, False)
                    alvallalkozo_obj, _ = Alvallalkozo.objects.get_or_create(
                        nev=get_cell_value(row, 14).strip()) if get_cell_value(row, 14) else (None, False)

                    master_item = None
                    existing = MasterItem.objects.filter(tetelszam=tetelszam_raw).first()
                    if existing:
                        if existing.leiras.strip() == leiras_raw.strip():
                            existing.fix_anyag_ar = import_ar;
                            existing.normaido = normaido;
                            existing.egyseg = egyseg;
                            if munkanem_obj: existing.munkanem = munkanem_obj
                            existing.save();
                            master_item = existing
                        else:
                            new_id = get_next_version_id(tetelszam_raw)
                            master_item = MasterItem.objects.create(tetelszam=new_id, leiras=leiras_raw, egyseg=egyseg,
                                                                    normaido=normaido, fix_anyag_ar=import_ar,
                                                                    munkanem=munkanem_obj, engy_kod=engy_kod,
                                                                    k_jelzo=k_jelzo, cpr_kod=cpr_kod)
                    else:
                        master_item = MasterItem.objects.create(tetelszam=tetelszam_raw, leiras=leiras_raw,
                                                                egyseg=egyseg, normaido=normaido,
                                                                fix_anyag_ar=import_ar, munkanem=munkanem_obj,
                                                                engy_kod=engy_kod, k_jelzo=k_jelzo, cpr_kod=cpr_kod)

                    Tetelsor.objects.update_or_create(
                        project=project, master_item=master_item,
                        defaults={
                            'sorszam': str(row_counter), 'mennyiseg': mennyiseg, 'anyag_egysegar': import_ar,
                            'alvallalkozo': alvallalkozo_obj, 'megjegyzes': megjegyzes,
                            'leiras': leiras_raw, 'egyseg': egyseg, 'normaido': normaido,
                            'munkanem': munkanem_obj, 'engy_kod': engy_kod, 'k_jelzo': k_jelzo, 'cpr_kod': cpr_kod,
                        }
                    )
                    row_counter += 1
            workbook.close();
            messages.success(request, "Sikeres import!");
        except Exception as e:
            messages.error(request, f"Hiba az import során: {e}")
        finally:
            if default_storage.exists(temp_file_path): default_storage.delete(temp_file_path)
        return redirect('project-detail', pk=project.id)
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        if not excel_file.name.endswith('.xlsx'): return redirect('project-detail', pk=project.id)
        temp_file_name = f"temp/{project.id}_{excel_file.name}";
        temp_file_path = default_storage.save(temp_file_name, excel_file)
        full_path = os.path.join(settings.MEDIA_ROOT, temp_file_path)
        try:
            workbook = openpyxl.load_workbook(full_path, read_only=True, data_only=True);
            sheet_names = workbook.sheetnames;
            workbook.close()
            context = {'project': project, 'sheet_names': sheet_names, 'temp_file_path': temp_file_path}
            return render(request, 'projects/import_step2_select.html', context)
        except Exception as e:
            if default_storage.exists(temp_file_path): default_storage.delete(temp_file_path)
            print(f"Hiba az Excel olvasásakor: {e}");
            return redirect('project-detail', pk=project.id)
    context = {'project': project};
    return render(request, 'projects/import_step1_upload.html', context)


# --- TÉTELSOR LÉTREHOZÁS TÖRZSBŐL ---
def tetelsor_create_from_master_step1(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = TetelsorCreateFromMasterForm(request.POST)
        if form.is_valid():
            master_id = form.cleaned_data['master_item'].id
            return redirect('tetelsor-create-master-step2', project_id=project.id, master_id=master_id)
    else:
        form = TetelsorCreateFromMasterForm()
    context = {'form': form, 'project': project}
    return render(request, 'projects/tetelsor_create_from_master.html', context)


def tetelsor_finalize_new(request, project_id, master_id):
    return tetelsor_create_from_master_step2(request, project_id, master_id)


def tetelsor_create_from_master_step2(request, project_id, master_id):
    project = get_object_or_404(Project, id=project_id)
    master = get_object_or_404(MasterItem, id=master_id)
    last_sorszam = Tetelsor.objects.filter(project=project).order_by('-sorszam').first()
    new_sorszam = int(last_sorszam.sorszam) + 1 if last_sorszam and last_sorszam.sorszam.isdigit() else 1
    initial_tetelsor = Tetelsor(
        project=project, master_item=master, sorszam=str(new_sorszam), mennyiseg=0,
        anyag_egysegar=master.fix_anyag_ar, leiras=master.leiras, egyseg=master.egyseg,
        normaido=master.normaido, munkanem=master.munkanem, engy_kod=master.engy_kod,
        k_jelzo=master.k_jelzo, cpr_kod=master.cpr_kod
    )
    if request.method == 'POST':
        form = TetelsorEditForm(request.POST, instance=initial_tetelsor)
        if form.is_valid():
            tetel = form.save(commit=False);
            tetel.project = project;
            tetel.master_item = master;
            tetel.sorszam = str(new_sorszam);
            tetel.save()
            messages.success(request, "Új tétel hozzáadva!")
            return redirect('project-detail', pk=project.id)
    else:
        form = TetelsorEditForm(instance=initial_tetelsor)
    context = {'form': form, 'project': project, 'tetelsor': initial_tetelsor}
    return render(request, 'projects/tetelsor_edit_form.html', context)


# --- CRUD Nézetek ---
def tetelsor_update_quantity(request, pk):
    tetelsor = get_object_or_404(Tetelsor, id=pk)
    if request.method == 'POST':
        form = TetelsorQuantityForm(request.POST, instance=tetelsor);
        if form.is_valid(): form.save(); return redirect('project-detail', pk=tetelsor.project.id)
    else:
        form = TetelsorQuantityForm(instance=tetelsor)
    context = {'form': form, 'tetelsor': tetelsor};
    return render(request, 'projects/tetelsor_form.html', context)


def tetelsor_update(request, pk):
    tetelsor = get_object_or_404(Tetelsor, id=pk)
    if request.method == 'POST':
        form = TetelsorEditForm(request.POST, instance=tetelsor);
        if form.is_valid(): form.save(); return redirect('project-detail', pk=tetelsor.project.id)
    else:
        form = TetelsorEditForm(instance=tetelsor)
    context = {'form': form, 'tetelsor': tetelsor};
    return render(request, 'projects/tetelsor_edit_form.html', context)


def tetelsor_delete(request, pk):
    tetelsor = get_object_or_404(Tetelsor, id=pk)
    project_id = tetelsor.project.id
    if request.method == 'POST': tetelsor.delete(); return redirect('project-detail', pk=project_id)
    context = {'tetelsor': tetelsor};
    return render(request, 'projects/tetelsor_confirm_delete.html', context)


# --- KIADÁS/NAPLÓ ---
def expense_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES);
        if form.is_valid():
            expense = form.save(commit=False);
            expense.project = project;
            expense.save()
            return redirect('project-detail', pk=project.id)
    else:
        form = ExpenseForm()
    context = {'form': form, 'project': project};
    return render(request, 'projects/expense_form.html', context)


def expense_update(request, pk):
    expense = get_object_or_404(Expense, id=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense);
        if form.is_valid(): form.save(); return redirect('project-detail', pk=expense.project.id)
    else:
        form = ExpenseForm(instance=expense)
    context = {'form': form, 'expense': expense, 'project': expense.project};
    return render(request, 'projects/expense_form.html', context)


def expense_delete(request, pk):
    expense = get_object_or_404(Expense, id=pk)
    project_id = expense.project.id
    if request.method == 'POST': expense.delete(); return redirect('project-detail', pk=project_id)
    context = {'expense': expense};
    return render(request, 'projects/expense_confirm_delete.html', context)


def daily_log_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = DailyLogForm(request.POST);
        if form.is_valid():
            log_entry = form.save(commit=False);
            log_entry.project = project;
            log_entry.save()
            return redirect('project-detail', pk=project.id)
    else:
        try:
            existing_log = DailyLog.objects.get(project=project, date=timezone.localdate()); form = DailyLogForm(
                instance=existing_log)
        except DailyLog.DoesNotExist:
            form = DailyLogForm(initial={'date': timezone.localdate()})
        except Exception:
            form = DailyLogForm()
    context = {'form': form, 'project': project};
    return render(request, 'projects/daily_log_form.html', context)


def daily_log_update(request, pk):
    log_entry = get_object_or_404(DailyLog, id=pk)
    if request.method == 'POST':
        form = DailyLogForm(request.POST, instance=log_entry);
        if form.is_valid(): form.save(); return redirect('project-detail', pk=log_entry.project.id)
    else:
        form = DailyLogForm(instance=log_entry)
    context = {'form': form, 'log_entry': log_entry, 'project': log_entry.project};
    return render(request, 'projects/daily_log_form.html', context)


def daily_log_delete(request, pk):
    log_entry = get_object_or_404(DailyLog, id=pk)
    project_id = log_entry.project.id
    if request.method == 'POST': log_entry.delete(); return redirect('project-detail', pk=project_id)
    context = {'log_entry': log_entry};
    return render(request, 'projects/daily_log_confirm_delete.html', context)


# === KATALÓGUS (MASTER ITEM) CRUD ===
def master_item_list(request):
    items = MasterItem.objects.all().order_by('tetelszam')
    q = request.GET.get('q')
    if q: items = items.filter(Q(leiras__icontains=q) | Q(tetelszam__icontains=q))
    if request.GET.get('munkanem'): items = items.filter(munkanem__id=request.GET.get('munkanem'))
    context = {'items': items, 'munkanemek': Munkanem.objects.all().order_by('nev'), 'search_query': q or "",
               'current_munkanem': int(request.GET.get('munkanem')) if request.GET.get('munkanem') else ""}
    return render(request, 'projects/master_item_list.html', context)


def master_item_create(r): f = MasterItemForm(r.POST or None); (f.save(), messages.success(r, "Tétel létrehozva!"),
                                                                redirect(
                                                                    'master-item-list')) if r.method == 'POST' and f.is_valid() else None; return render(
    r, 'projects/master_item_form.html', {'form': f, 'title': 'Új Tétel'})


def master_item_update(r, pk): i = get_object_or_404(MasterItem, id=pk); f = MasterItemForm(r.POST or None,
                                                                                            instance=i); (
f.save(), messages.success(r, "Tétel frissítve!"),
redirect('master-item-list')) if r.method == 'POST' and f.is_valid() else None; return render(r,
                                                                                              'projects/master_item_form.html',
                                                                                              {'form': f,
                                                                                               'title': 'Tétel Szerkesztése'})


def master_item_delete(r, pk): i = get_object_or_404(MasterItem, id=pk); (
i.delete(), messages.success(r, "Tétel törölve."),
redirect('master-item-list')) if r.method == 'POST' else None; return render(r,
                                                                             'projects/master_item_confirm_delete.html',
                                                                             {'item': i})


def master_item_components(r, pk):
    m = get_object_or_404(MasterItem, id=pk);
    f = ItemComponentForm(r.POST or None)
    if r.method == 'POST' and f.is_valid(): c = f.save(
        commit=False); c.master_item = m; c.save(); m.fix_anyag_ar = m.calculated_material_cost; m.save(); messages.success(
        r, "Anyag hozzáadva!"); return redirect('master-item-components', pk=m.id)
    return render(r, 'projects/master_item_components.html',
                  {'master_item': m, 'components': m.components.all(), 'form': f})


def master_item_component_delete(r, pk): c = get_object_or_404(ItemComponent,
                                                               id=pk); m = c.master_item; c.delete(); m.fix_anyag_ar = m.calculated_material_cost; m.save(); messages.success(
    r, "Anyag eltávolítva."); return redirect('master-item-components', pk=m.id)