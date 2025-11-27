# projects/views.py

from django.shortcuts import render, get_object_or_404, redirect
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
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.contrib.staticfiles import finders

# Modellek importálása
from .models import (
    Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog,
    Supplier, Material, MasterItem, ItemComponent, CompanySettings,
    ProjectDocument, MaterialOrder, OrderItem, ProjectInventory, DailyMaterialUsage,
    GanttLink, UniclassNode
)

# Űrlapok importálása
from .forms import (
    ProjectForm, TetelsorQuantityForm, TetelsorEditForm, ExpenseForm,
    DailyLogForm, TetelsorCreateFromMasterForm, MasterItemForm, ItemComponentForm,
    ProjectDocumentForm, MaterialOrderForm, OrderItemFormSet, DailyMaterialUsageFormSet,
    TaskForm
)

try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# --- SEGÉDFÜGGVÉNYEK ---

def calculate_work_end_date(start_date, workdays):
    """ Munkanapok alapján számolja a befejezést (H-P). """
    if not start_date or workdays <= 0: return None
    current_date = start_date
    days_to_add = int(workdays) - 1

    while current_date.weekday() >= 5:
        current_date += timedelta(days=1)

    added_days = 0
    while added_days < days_to_add:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:
            added_days += 1

    return current_date


def get_cell_value(row, index, default=""):
    try:
        val = row[index].value; return str(val).strip() if val is not None else default
    except:
        return default


def get_cell_decimal(row, index):
    try:
        val = row[index].value
        if val is None: return Decimal(0)
        if isinstance(val, (int, float, Decimal)): return Decimal(val)
        val_str = str(val).replace("\xa0", "").replace(" ", "").replace("Ft", "").replace(",", ".")
        return Decimal(val_str) if val_str else Decimal(0)
    except:
        return Decimal(0)


def get_next_version_id(base_id):
    counter = 1
    while True:
        new_id = f"{base_id}-E_{counter:03d}"
        if not MasterItem.objects.filter(tetelszam=new_id).exists(): return new_id
        counter += 1


def get_company_context():
    settings_obj = CompanySettings.objects.first()
    if settings_obj:
        logo_path = settings_obj.logo.path if settings_obj.logo else None
        if logo_path: logo_path = logo_path.replace('\\', '/')
        return {
            'company_name': settings_obj.name,
            'company_address': settings_obj.full_address(),
            'company_tax': settings_obj.tax_number,
            'company_phone': settings_obj.phone,
            'company_email': settings_obj.email,
            'company_logo': settings_obj.logo,
            'company_logo_path': logo_path,
            'signatories': settings_obj.signatories.all(),
            'default_city': settings_obj.head_city,
            'company_sites': settings_obj.sites.all()
        }
    return {'company_name': 'Saját Kft.', 'company_address': '-', 'company_tax': '-', 'company_phone': '-',
            'company_email': '-', 'company_logo': None, 'company_logo_path': None, 'signatories': [],
            'default_city': 'Budapest', 'company_sites': []}


def link_callback(uri, rel):
    if uri.startswith('data:') or os.path.exists(uri): return uri
    result = finders.find(uri)
    if result: return result[0] if isinstance(result, (list, tuple)) else result
    sUrl = settings.STATIC_URL;
    sRoot = settings.STATIC_ROOT
    mUrl = settings.MEDIA_URL;
    mRoot = settings.MEDIA_ROOT
    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri
    return path if os.path.isfile(path) else uri


# --- FŐ NÉZETEK ---

def project_list(request):
    projects = Project.objects.exclude(status='TORLES_KERELEM').order_by('start_date')
    q = request.GET.get('q')
    if q: projects = projects.filter(Q(name__icontains=q) | Q(location__icontains=q) | Q(client__icontains=q))

    project_groups = []
    if q:
        if projects.exists(): project_groups.append({'label': f"Keresés: '{q}'", 'projects': projects})
    else:
        for sc, sl in Project.STATUS_CHOICES:
            projs = projects.filter(status=sc)
            if projs.exists(): project_groups.append({'label': sl, 'projects': projs})

    # ITT A LÉNYEG: Explicit kulcsnevek (ls, la) használata
    all_budgets = Tetelsor.objects.filter(project__in=projects).aggregate(
        mat=Sum('anyag_osszesen'),
        ls=Sum('sajat_munkadij_osszesen'),  # ls = Labor Sajat
        la=Sum('alv_munkadij_osszesen')  # la = Labor Alvallalkozo
    )

    # És itt hivatkozunk rájuk:
    global_plan = (all_budgets['mat'] or 0) + (all_budgets['ls'] or 0) + (all_budgets['la'] or 0)

    global_spent = Expense.objects.filter(project__in=projects).aggregate(s=Sum('amount_netto'))['s'] or 0
    global_balance = global_plan - global_spent

    # Feladatok
    tasks = Task.objects.filter(status='FUGGO').order_by('due_date')

    if request.method == 'POST' and 'task_submit' in request.POST:
        task_form = TaskForm(request.POST)
        if task_form.is_valid():
            task_form.save()
            messages.success(request, "Feladat hozzáadva!")
            return redirect('project-list')
    else:
        task_form = TaskForm()

    status_counts = {
        'TERVEZES': projects.filter(status__in=['UJ_KERES', 'FELMERES', 'AJANLAT', 'ELOKESZITES']).count(),
        'FOLYAMATBAN': projects.filter(status='KIVITELEZES').count(),
        'BEFEJEZETT': projects.filter(status='ATADAS').count(),
        'LEZART': projects.filter(status__in=['LEZART', 'ELUTASITVA']).count(),
    }

    context = {
        'project_groups': project_groups, 'global_plan': global_plan, 'global_spent': global_spent,
        'global_balance': global_balance, 'status_counts': status_counts, 'search_query': q or "",
        'tasks': tasks, 'task_form': task_form
    }
    return render(request, 'projects/project_list.html', context)


def task_complete(request, pk):
    task = get_object_or_404(Task, id=pk)
    task.status = 'KESZ'
    task.save()
    messages.success(request, "Feladat elvégezve!")
    return redirect('project-list')


def project_detail(request, pk):
    project = get_object_or_404(Project, id=pk)
    tasks = project.tetelsorok.all().order_by('sorszam')
    expenses = project.expenses.all().order_by('-date')
    documents = project.documents.all().order_by('-uploaded_at')
    orders = project.material_orders.all().order_by('-date')

    try:
        inventory = project.inventory.all().order_by('name')
    except AttributeError:
        inventory = []

    if request.GET.get('expense_category_filter'): expenses = expenses.filter(
        category=request.GET.get('expense_category_filter'))
    if request.GET.get('munkanem_filter'): tasks = tasks.filter(munkanem__nev=request.GET.get('munkanem_filter'))

    munkanem_list = Munkanem.objects.all().order_by('nev')
    expense_category_list = Expense.CATEGORY_CHOICES

    summ = tasks.aggregate(mat=Sum('anyag_osszesen'), ls=Sum('sajat_munkadij_osszesen'),
                           la=Sum('alv_munkadij_osszesen'), hours=Sum(F('mennyiseg') * F('normaido')))
    plan_mat = summ['mat'] or 0;
    plan_ls = summ['ls'] or 0;
    plan_la = summ['la'] or 0;
    plan_total = plan_mat + plan_ls + plan_la
    spent = expenses.aggregate(s=Sum('amount_netto'))['s'] or 0
    hours = summ['hours'] or 0;
    hpd = project.hours_per_day;
    days = math.ceil(hours / (project.hours_per_day or 8)) if project.hours_per_day else 0
    end_date = calculate_work_end_date(project.start_date, days)

    context = {
        'project': project, 'tasks': tasks, 'expenses': expenses, 'documents': documents, 'orders': orders,
        'inventory': inventory,
        'plan_anyag': plan_mat, 'plan_dij': plan_ls + plan_la, 'plan_total': plan_total,
        'actual_total': spent, 'balance': plan_total - spent,
        'vat_rate': project.vat_rate, 'total_vat': plan_total * (project.vat_rate / 100),
        'total_project_brutto': plan_total * (1 + project.vat_rate / 100),
        'total_effort_hours': hours, 'total_workdays': days,
        'calculated_end_date': end_date,
        'munkanem_list': munkanem_list,
        'expense_category_list': expense_category_list,
        'current_munkanem': request.GET.get('munkanem_filter'),
        'current_expense_category': request.GET.get('expense_category_filter'),
        'all_statuses': Project.STATUS_CHOICES
    }
    return render(request, 'projects/project_detail.html', context)


def project_status_update(request, pk, status_code):
    project = get_object_or_404(Project, id=pk)
    valid_codes = [c[0] for c in Project.STATUS_CHOICES]
    if status_code in valid_codes:
        project.status = status_code
        project.save()
        messages.success(request, f"Státusz frissítve: {project.get_status_display()}")
    else:
        messages.error(request, "Érvénytelen státusz!")
    return redirect('project-detail', pk=project.id)


# === GANTT DIAGRAM LOGIKA ===

def gantt_view(request, project_id):
    # Átadjuk az alvállalkozókat is a legördülő listához
    project = get_object_or_404(Project, id=project_id)
    alvallalkozok = Alvallalkozo.objects.all().values('id', 'nev')
    return render(request, 'projects/gantt_view.html', {
        'project': project,
        'alvallalkozok': list(alvallalkozok)
    })


def gantt_data(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = project.tetelsorok.all().order_by('sorszam')
    data = []

    for t in tasks:
        start = project.start_date or timezone.now().date()

        # --- 1. IDŐTARTAM SZÁMÍTÁS (AUTOMATIKUS) ---
        calc_duration = 1
        if t.normaido and t.mennyiseg:
            try:
                norma = float(t.normaido)
                mennyiseg = float(t.mennyiseg)
                hpd = float(project.hours_per_day or 8)
                if hpd > 0 and norma > 0 and mennyiseg > 0:
                    total_hours = mennyiseg * norma
                    calc_duration = math.ceil(total_hours / hpd)
            except (ValueError, TypeError):
                pass

        # --- 2. DÖNTÉS: HASZNÁLJUK-E A MENTETTET? ---
        duration = 1

        # Ha a tételnek van mentett kezdési dátuma (tehát már szerkesztették a Gantt-on)
        if t.gantt_start_date:
            # Ha a mentett időtartam > 1 (tehát kézzel átírták), akkor az nyer
            if t.gantt_duration and t.gantt_duration > 1:
                duration = t.gantt_duration
            # Ha a mentett 1 (alapértelmezett), de a számított több, akkor a számított nyer (ez javítja a hibát!)
            elif calc_duration > 1:
                duration = calc_duration
            else:
                duration = 1
        else:
            # Ha még nem szerkesztették (nincs start date), akkor a számított
            duration = calc_duration

        if duration < 1: duration = 1
        # --------------------------------------------

        txt = t.leiras if t.leiras else (t.master_item.leiras if t.master_item else "-")
        tszam = t.master_item.tetelszam if t.master_item else (t.sorszam if t.sorszam else "")
        mn = t.munkanem.nev if t.munkanem else "-"

        # Kezdés
        start_date_obj = t.gantt_start_date if t.gantt_start_date else start
        start_date_str = start_date_obj.strftime("%Y-%m-%d")

        # Befejezés (számított)
        finish_date_obj = calculate_work_end_date(start_date_obj, duration)
        finish_date_str = finish_date_obj.strftime("%Y-%m-%d") if finish_date_obj else ""

        data.append({
            'id': t.id,
            'text': f"{tszam} - {txt[:30]}...",
            'start_date': start_date_str,
            'finish_date': finish_date_str,
            'duration': duration,
            'progress': float(t.progress_percentage) / 100 if t.progress_percentage else 0,
            'open': True,
            'mennyiseg': f"{t.mennyiseg} {t.egyseg}",
            'munkanem': mn,
            'felelos': t.felelos or "",
            'owner_id': t.alvallalkozo.id if t.alvallalkozo else ""
        })

    # Linkek
    link_data = []
    try:
        links = GanttLink.objects.filter(source__project=project)
        link_data = [{'id': l.id, 'source': l.source.id, 'target': l.target.id, 'type': l.type} for l in links]
    except Exception:
        pass

    return JsonResponse({"data": data, "links": link_data})


@csrf_exempt
def gantt_update(request, project_id):
    """ GANTT MENTÉS (OKOS PARAMÉTER-KEZELÉSSEL) """
    if request.method == 'POST':
        try:
            # Paraméterek keresése POST-ban és GET-ben is
            mode = request.POST.get("gantt_mode") or request.GET.get("gantt_mode")
            op = request.POST.get("!nativeeditor_status")
            sid = request.POST.get("id")

            # Link detektálás
            is_link = ('source' in request.POST and 'target' in request.POST) or (mode == 'link')

            if is_link:
                if op == "inserted":
                    source = get_object_or_404(Tetelsor, id=request.POST.get("source"))
                    target = get_object_or_404(Tetelsor, id=request.POST.get("target"))
                    link = GanttLink.objects.create(source=source, target=target, type=request.POST.get("type", "0"))
                    return JsonResponse({"action": "inserted", "tid": link.id})
                elif op == "deleted":
                    GanttLink.objects.filter(id=sid).delete()
                    return JsonResponse({"action": "deleted"})
                elif op == "updated":
                    link = get_object_or_404(GanttLink, id=sid)
                    link.type = request.POST.get("type", "0")
                    link.save()
                    return JsonResponse({"action": "updated"})

            else:  # TASK
                if op == "updated":
                    task = get_object_or_404(Tetelsor, id=sid)
                    if "start_date" in request.POST:
                        task.gantt_start_date = request.POST.get("start_date")[:10]
                    if "duration" in request.POST:
                        task.gantt_duration = int(request.POST.get("duration"))
                    if "progress" in request.POST:
                        task.progress_percentage = float(request.POST.get("progress")) * 100

                    # ÚJ MEZŐK MENTÉSE
                    if "felelos" in request.POST:
                        task.felelos = request.POST.get("felelos")
                    if "owner_id" in request.POST:  # Alvállalkozó
                        aid = request.POST.get("owner_id")
                        task.alvallalkozo = Alvallalkozo.objects.get(id=aid) if aid else None

                    task.save()
                    return JsonResponse({"action": "updated"})

                elif op == "inserted":
                    return JsonResponse({"action": "error", "msg": "Új tételt a Költségvetésben vegyél fel!"})

        except Exception as e:
            print(f"GANTT HIBA: {e}")  # Debug
            return JsonResponse({"action": "error", "msg": str(e)})

    return JsonResponse({"action": "error"})


# === ÚJ: SZINKRONIZÁLÁS TÖRZZSEL ===
def sync_tetelsor_to_master(request, pk):
    tetelsor = get_object_or_404(Tetelsor, id=pk)
    if not tetelsor.master_item:
        messages.error(request, "Ez a tétel nem csatolt a törzshöz!")
        return redirect('project-detail', pk=tetelsor.project.id)

    master = tetelsor.master_item
    master.leiras = tetelsor.leiras
    master.normaido = tetelsor.normaido
    master.fix_anyag_ar = tetelsor.anyag_egysegar
    master.egyseg = tetelsor.egyseg
    master.save()

    messages.success(request, f"A '{master.tetelszam}' törzs tétel frissítve!")
    return redirect('project-detail', pk=tetelsor.project.id)


def project_quote_html(request, pk):
    project = get_object_or_404(Project, id=pk)
    tasks = project.tetelsorok.all().order_by('sorszam')
    summary = tasks.aggregate(mat=Sum('anyag_osszesen'), ls=Sum('sajat_munkadij_osszesen'),
                              la=Sum('alv_munkadij_osszesen'))
    netto = (summary['mat'] or 0) + (summary['ls'] or 0) + (summary['la'] or 0)
    vat_amount = total_netto * (project.vat_rate / Decimal(100))
    total_brutto = total_netto + vat_amount
    company_data = get_company_context()
    context = {
        'project': project, 'tasks': tasks, 'total_netto': total_netto,
        'vat_amount': vat_amount, 'total_brutto': total_brutto,
        'today': timezone.now(), **company_data
    }
    return render(request, 'projects/quote_print.html', context)


def project_quote_pdf(request, pk):
    return project_quote_html(request, pk)


# --- CRUD ---
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            new_project = form.save()
            return redirect('project-detail', pk=new_project.id)
    else:
        form = ProjectForm()
    context = {'form': form}
    return render(request, 'projects/project_form.html', context)


def project_update(request, pk):
    project = get_object_or_404(Project, id=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            if 'hourly_rate' in form.changed_data:
                for t in project.tetelsorok.all(): t.save()
            return redirect('project-detail', pk=project.id)
    else:
        form = ProjectForm(instance=project)
    context = {'form': form, 'project': project}
    return render(request, 'projects/project_form.html', context)


def project_request_deletion(request, pk):
    project = get_object_or_404(Project, id=pk)
    if request.method == 'POST':
        project.status = 'TORLES_KERELEM'
        project.save()
        return redirect('project-list')
    context = {'project': project}
    return render(request, 'projects/project_confirm_delete.html', context)


# --- IMPORT ---
def import_tasks(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST' and 'temp_file_path' in request.POST:
        path = os.path.join(settings.MEDIA_ROOT, request.POST.get('temp_file_path'))
        wb = openpyxl.load_workbook(path, data_only=True)
        cnt = 1
        try:
            for sheet in request.POST.getlist('sheets'):
                if sheet not in wb.sheetnames: continue
                ws = wb[sheet]
                for row in ws.iter_rows(min_row=2):
                    tid = get_cell_value(row, 1);
                    if not tid: continue
                    desc = get_cell_value(row, 2);
                    qty = get_cell_decimal(row, 3);
                    unit = get_cell_value(row, 4);
                    price = get_cell_decimal(row, 5)
                    mn = Munkanem.objects.get_or_create(nev=get_cell_value(row, 12).strip())[0] if get_cell_value(row,
                                                                                                                  12) else None
                    alv = Alvallalkozo.objects.get_or_create(nev=get_cell_value(row, 14).strip())[0] if get_cell_value(
                        row, 14) else None
                    mi = MasterItem.objects.filter(tetelszam=tid).first()
                    if not mi:
                        mi = MasterItem.objects.create(tetelszam=tid, leiras=desc, egyseg=unit,
                                                       normaido=get_cell_decimal(row, 13), fix_anyag_ar=price,
                                                       munkanem=mn)
                    elif mi.leiras.strip() != desc.strip():
                        mi = MasterItem.objects.create(tetelszam=get_next_version_id(tid), leiras=desc, egyseg=unit,
                                                       normaido=get_cell_decimal(row, 13), fix_anyag_ar=price,
                                                       munkanem=mn)
                    Tetelsor.objects.update_or_create(
                        project=project, master_item=mi,
                        defaults={'sorszam': str(cnt), 'mennyiseg': qty, 'anyag_egysegar': price, 'leiras': desc,
                                  'egyseg': unit, 'normaido': get_cell_decimal(row, 13), 'munkanem': mn,
                                  'alvallalkozo': alv}
                    )
                    cnt += 1
            wb.close();
            messages.success(request, "Sikeres import!")
        except Exception as e:
            messages.error(request, f"Hiba: {e}")
        finally:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        return redirect('project-detail', pk=project.id)

    if request.method == 'POST' and request.FILES.get('excel_file'):
        f = request.FILES['excel_file']
        path = default_storage.save(f"temp/{f.name}", f)
        wb = openpyxl.load_workbook(os.path.join(settings.MEDIA_ROOT, path), read_only=True)
        return render(request, 'projects/import_step2_select.html',
                      {'project': project, 'sheet_names': wb.sheetnames, 'temp_file_path': path})
    return render(request, 'projects/import_step1_upload.html', {'project': project})


def tetelsor_create_from_master_step1(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    items = MasterItem.objects.all().order_by('tetelszam')
    q = request.GET.get('q')
    if q: items = items.filter(Q(leiras__icontains=q) | Q(tetelszam__icontains=q))
    mn = request.GET.get('munkanem')
    if mn: items = items.filter(munkanem__id=mn)
    return render(request, 'projects/tetelsor_create_from_master.html',
                  {'project': project, 'items': items, 'munkanemek': Munkanem.objects.all().order_by('nev'),
                   'search_query': q or "", 'current_munkanem': int(mn) if mn else ""})


def tetelsor_finalize_new(request, project_id, master_id):
    return tetelsor_create_from_master_step2(request, project_id, master_id)


def tetelsor_create_from_master_step2(request, project_id, master_id):
    project = get_object_or_404(Project, id=project_id)
    master = get_object_or_404(MasterItem, id=master_id)
    last_sorszam = Tetelsor.objects.filter(project=project).order_by('-sorszam').first()
    new_sorszam = 1
    if last_sorszam:
        try:
            parts = last_sorszam.sorszam.split('-')
            if len(parts) > 1 and parts[-1].isdigit():
                new_sorszam = int(parts[-1]) + 1
            elif last_sorszam.sorszam.isdigit():
                new_sorszam = int(last_sorszam.sorszam) + 1
        except:
            pass

    t = Tetelsor(
        project=project, master_item=master, sorszam=str(new_sorszam),
        mennyiseg=0, anyag_egysegar=master.fix_anyag_ar,
        leiras=master.leiras, egyseg=master.egyseg, normaido=master.normaido,
        munkanem=master.munkanem, engy_kod=master.engy_kod, k_jelzo=master.k_jelzo, cpr_kod=master.cpr_kod
    )

    if request.method == 'POST':
        form = TetelsorEditForm(request.POST, instance=t)
        if form.is_valid():
            tetel = form.save(commit=False)
            tetel.project = project;
            tetel.master_item = master
            if not tetel.sorszam: tetel.sorszam = str(new_sorszam)
            tetel.save()
            messages.success(request, "Tétel beillesztve!")
            return redirect('project-detail', pk=project.id)
    else:
        form = TetelsorEditForm(instance=t)

    context = {
        'form': form, 'project': project, 'tetelsor': t,
        'submit_label': 'Beillesztés Költségvetésbe'
    }
    return render(request, 'projects/tetelsor_edit_form.html', context)


# --- CRUD Nézetek ---
def tetelsor_update_quantity(request, pk):
    t = get_object_or_404(Tetelsor, id=pk)
    if request.method == 'POST':
        form = TetelsorQuantityForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            return redirect('project-detail', pk=t.project.id)
    else:
        form = TetelsorQuantityForm(instance=t)
    context = {'form': form, 'tetelsor': t, 'project': t.project};
    return render(request, 'projects/tetelsor_form.html', context)


def tetelsor_update(request, pk):
    t = get_object_or_404(Tetelsor, id=pk)
    if request.method == 'POST':
        form = TetelsorEditForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            return redirect('project-detail', pk=t.project.id)
    else:
        form = TetelsorEditForm(instance=t)
    context = {'form': form, 'tetelsor': t, 'project': t.project};
    return render(request, 'projects/tetelsor_edit_form.html', context)


def tetelsor_delete(request, pk):
    t = get_object_or_404(Tetelsor, id=pk)
    pid = t.project.id
    if request.method == 'POST':
        t.delete()
        return redirect('project-detail', pk=pid)
    context = {'tetelsor': t};
    return render(request, 'projects/tetelsor_confirm_delete.html', context)


def expense_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.project = project
            exp.save()
            return redirect('project-detail', pk=project.id)
    else:
        form = ExpenseForm()
    context = {'form': form, 'project': project};
    return render(request, 'projects/expense_form.html', context)


def expense_update(request, pk):
    e = get_object_or_404(Expense, id=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=e)
        if form.is_valid():
            form.save()
            return redirect('project-detail', pk=e.project.id)
    else:
        form = ExpenseForm(instance=e)
    context = {'form': form, 'expense': e, 'project': e.project};
    return render(request, 'projects/expense_form.html', context)


def expense_delete(request, pk):
    e = get_object_or_404(Expense, id=pk)
    pid = e.project.id
    if request.method == 'POST':
        e.delete()
        return redirect('project-detail', pk=pid)
    context = {'expense': e};
    return render(request, 'projects/expense_confirm_delete.html', context)


def daily_log_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        form = DailyLogForm(request.POST)
        formset = DailyMaterialUsageFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            log = form.save(commit=False)
            log.project = project
            log.save()

            usages = formset.save(commit=False)
            for usage in usages:
                usage.log = log
                usage.save()
                if usage.inventory_item:
                    usage.inventory_item.quantity -= usage.quantity
                    usage.inventory_item.save()

            return redirect('project-detail', pk=project.id)
    else:
        try:
            existing = DailyLog.objects.get(project=project, date=timezone.localdate())
            return redirect('daily-log-update', pk=existing.id)
        except DailyLog.DoesNotExist:
            form = DailyLogForm(initial={'date': timezone.localdate()})
            formset = DailyMaterialUsageFormSet(form_kwargs={'project': project})

    return render(request, 'projects/daily_log_form.html', {
        'form': form, 'formset': formset, 'project': project
    })


def daily_log_update(request, pk):
    log = get_object_or_404(DailyLog, id=pk)
    project = log.project

    if request.method == 'POST':
        form = DailyLogForm(request.POST, instance=log)
        formset = DailyMaterialUsageFormSet(request.POST, instance=log, form_kwargs={'project': project})

        if form.is_valid() and formset.is_valid():
            form.save()
            usages = formset.save(commit=False)
            for usage in usages:
                if not usage.pk:
                    usage.log = log
                    usage.save()
                    if usage.inventory_item:
                        usage.inventory_item.quantity -= usage.quantity
                        usage.inventory_item.save()
                else:
                    usage.save()

            for obj in formset.deleted_objects:
                obj.delete()

            return redirect('project-detail', pk=project.id)
    else:
        form = DailyLogForm(instance=log)
        formset = DailyMaterialUsageFormSet(instance=log, form_kwargs={'project': project})

    return render(request, 'projects/daily_log_form.html', {
        'form': form, 'formset': formset, 'log_entry': log, 'project': project
    })


def daily_log_delete(request, pk):
    l = get_object_or_404(DailyLog, id=pk)
    pid = l.project.id
    if request.method == 'POST':
        l.delete()
        return redirect('project-detail', pk=pid)
    context = {'log_entry': l};
    return render(request, 'projects/daily_log_confirm_delete.html', context)


# --- KATALÓGUS (MASTER ITEM) CRUD ---
def master_item_list(request):
    items = MasterItem.objects.all().order_by('tetelszam')
    q = request.GET.get('q')
    if q: items = items.filter(Q(leiras__icontains=q) | Q(tetelszam__icontains=q))
    if request.GET.get('munkanem'): items = items.filter(munkanem__id=request.GET.get('munkanem'))
    context = {'items': items, 'munkanemek': Munkanem.objects.all().order_by('nev'), 'search_query': q or "",
               'current_munkanem': int(request.GET.get('munkanem')) if request.GET.get('munkanem') else ""}
    return render(request, 'projects/master_item_list.html', context)


def master_item_create(request):
    if request.method == 'POST':
        form = MasterItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tétel létrehozva!")
            return redirect('master-item-list')
    else:
        form = MasterItemForm()
    return render(request, 'projects/master_item_form.html', {'form': form, 'title': 'Új Tétel'})


def master_item_update(request, pk):
    item = get_object_or_404(MasterItem, id=pk)
    if request.method == 'POST':
        form = MasterItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Tétel frissítve!")
            return redirect('master-item-list')
    else:
        form = MasterItemForm(instance=item)
    return render(request, 'projects/master_item_form.html', {'form': form, 'title': 'Szerkesztés'})


def master_item_delete(request, pk):
    item = get_object_or_404(MasterItem, id=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Tétel törölve.")
        return redirect('master-item-list')
    return render(request, 'projects/master_item_confirm_delete.html', {'item': item})


def master_item_components(request, pk):
    master_item = get_object_or_404(MasterItem, id=pk)
    components = master_item.components.all()

    if request.method == 'POST':
        form = ItemComponentForm(request.POST)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.master_item = master_item
            comp.save()
            master_item.fix_anyag_ar = master_item.calculated_material_cost
            master_item.save()
            messages.success(request, "Anyag hozzáadva! Ár frissítve.")
            return redirect('master-item-components', pk=master_item.id)
    else:
        form = ItemComponentForm()

    context = {
        'master_item': master_item,
        'components': components,
        'form': form
    }
    return render(request, 'projects/master_item_components.html', context)


def master_item_component_delete(request, pk):
    comp = get_object_or_404(ItemComponent, id=pk)
    master_id = comp.master_item.id
    master_item = comp.master_item
    comp.delete()
    master_item.fix_anyag_ar = master_item.calculated_material_cost
    master_item.save()
    messages.success(request, "Anyag eltávolítva.")
    return redirect('master-item-components', pk=master_id)


# === KATALÓGUS IMPORT ===
def import_master_items(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        path = default_storage.save(f"temp/{excel_file.name}", excel_file)
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        try:
            wb = openpyxl.load_workbook(full_path, data_only=True)
            for sheet_name in workbook.sheetnames:
                ws = workbook[sheet_name]
                for row in ws.iter_rows(min_row=2):
                    tetelszam = get_cell_value(row, 1)
                    if not tetelszam: continue

                    munkanem_obj = None
                    mn_nev = get_cell_value(row, 12)
                    if mn_nev: munkanem_obj, _ = Munkanem.objects.get_or_create(nev=mn_nev.strip())

                    MasterItem.objects.update_or_create(
                        tetelszam=tetelszam,
                        defaults={
                            'leiras': get_cell_value(row, 2),
                            'egyseg': get_cell_value(row, 4),
                            'fix_anyag_ar': get_cell_decimal(row, 5),
                            'normaido': get_cell_decimal(row, 13),
                            'munkanem': munkanem_obj,
                            'engy_kod': get_cell_value(row, 10),
                            'k_jelzo': get_cell_value(row, 11),
                            'cpr_kod': get_cell_value(row, 15)
                        }
                    )
            workbook.close()
            messages.success(request, "Katalógus sikeresen frissítve!")
        except Exception as e:
            messages.error(request, f"Hiba: {e}")
        finally:
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except:
                    pass
        return redirect('master-item-list')
    return render(request, 'projects/master_item_import.html')


# === DOKUMENTUM KEZELÉS ===
def document_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = ProjectDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.project = project
            doc.save()
            messages.success(request, "Dokumentum feltöltve!")
            return redirect('project-detail', pk=project.id)
    else:
        form = ProjectDocumentForm()
    return render(request, 'projects/document_form.html', {'form': form, 'project': project})


def document_delete(request, pk):
    doc = get_object_or_404(ProjectDocument, id=pk)
    pid = doc.project.id
    if request.method == 'POST':
        doc.delete()
        messages.success(request, "Dokumentum törölve.")
        return redirect('project-detail', pk=pid)
    return render(request, 'projects/document_confirm_delete.html', {'document': doc})


# === ANYAGRENDELÉS ===
def material_order_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = MaterialOrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.project = project
            order.save()
            items = formset.save(commit=False)
            for item in items:
                item.order = order
                item.save()
            for obj in formset.deleted_objects: obj.delete()
            return redirect('project-detail', pk=project.id)
    else:
        form = MaterialOrderForm()
        formset = OrderItemFormSet()
    return render(request, 'projects/material_order_form.html',
                  {'form': form, 'formset': formset, 'project': project, 'title': 'Új Rendelés'})


def material_order_update(request, pk):
    order = get_object_or_404(MaterialOrder, id=pk)
    if request.method == 'POST':
        form = MaterialOrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('project-detail', pk=order.project.id)
    else:
        form = MaterialOrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    return render(request, 'projects/material_order_form.html',
                  {'form': form, 'formset': formset, 'project': order.project, 'title': 'Rendelés Szerkesztése'})


def material_order_delete(request, pk):
    order = get_object_or_404(MaterialOrder, id=pk)
    pid = order.project.id
    if request.method == 'POST':
        order.delete()
        return redirect('project-detail', pk=pid)
    return render(request, 'projects/document_confirm_delete.html', {'document': order})


def material_order_create_from_budget(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = project.tetelsorok.filter(anyag_egysegar__gt=0).order_by('sorszam')
    if request.method == 'POST':
        ids = request.POST.getlist('selected_items')
        if ids:
            order = MaterialOrder.objects.create(project=project, status='TERVEZET', notes="Költségvetésből generálva")
            for tid in ids:
                t = Tetelsor.objects.get(id=tid)
                OrderItem.objects.create(
                    order=order,
                    name=t.leiras,
                    quantity=t.mennyiseg,
                    unit=t.egyseg,
                    price=t.anyag_egysegar
                )
            return redirect('material-order-update', pk=order.id)
    return render(request, 'projects/material_order_from_budget.html', {'project': project, 'tasks': tasks})


def material_order_print(request, pk):
    order = get_object_or_404(MaterialOrder, id=pk)
    total_value = sum(item.total_price for item in order.items.all())
    context = {'order': order, 'items': order.items.all(), 'total_value': total_value, 'today': timezone.now(),
               **get_company_context()}
    return render(request, 'projects/material_order_print.html', context)


def material_order_pdf(request, pk):
    return material_order_print(request, pk)


def material_order_finalize(request, pk):
    order = get_object_or_404(MaterialOrder, id=pk)
    if request.method == 'POST':
        total = sum(i.total_price for i in order.items.all())
        if total > 0:
            Expense.objects.create(project=order.project, name=f"Rendelés #{order.id}", date=timezone.now(),
                                   category='ANYAG', amount_netto=total)

        # Készletnövelés
        for item in order.items.all():
            inv_item, created = ProjectInventory.objects.get_or_create(
                project=order.project, name=item.name, defaults={'unit': item.unit}
            )
            inv_item.quantity += item.quantity
            inv_item.save()

        order.status = 'TELJESITVE'
        order.save()
        messages.success(request, "Rendelés lezárva és könyvelve!")
        return redirect('project-detail', pk=order.project.id)
    return render(request, 'projects/material_order_finalize.html', {'order': order})


# projects/views.py (A fájl végére illeszd be)

# === GLOBÁLIS GANTT (CÉGSZINTŰ) ===

def global_gantt_view(request):
    # Alvállalkozók a legördülőhöz
    alvallalkozok = Alvallalkozo.objects.all().values('id', 'nev')
    return render(request, 'projects/global_gantt.html', {
        'alvallalkozok': list(alvallalkozok)
    })


def global_gantt_data(request):
    # 1. PROJEKTEK LEKÉRÉSE (Mint "Szülő" elemek)
    # Csak a nem törölt projektek kellenek
    projects = Project.objects.exclude(status='TORLES_KERELEM').order_by('start_date')

    data = []

    # Projektek hozzáadása a listához
    for p in projects:
        start = p.start_date or timezone.now().date()
        # A projekt egy "gyűjtő" feladat lesz
        data.append({
            'id': f"prj_{p.id}",  # Egyedi ID prefix
            'text': p.name,
            'start_date': start.strftime("%Y-%m-%d"),
            'type': 'project',  # DHTMLX speciális típus
            'open': False,  # Alapból összecsukva (vagy True ha nyitva akarod)
            'readonly': True  # A projekt nevét/idejét itt ne szerkesszék, az számolódjon
        })

    # 2. FELADATOK LEKÉRÉSE (Mint "Gyerek" elemek)
    tasks = Tetelsor.objects.filter(project__in=projects).order_by('sorszam')

    for t in tasks:
        start = t.project.start_date or timezone.now().date()

        # Időtartam logika (ugyanaz, mint az egyedinél)
        duration = 1
        if t.gantt_start_date and t.gantt_duration and t.gantt_duration > 0:
            duration = t.gantt_duration
        elif t.normaido and t.mennyiseg:
            try:
                hpd = float(t.project.hours_per_day or 8)
                total = float(t.mennyiseg) * float(t.normaido)
                if hpd > 0: duration = math.ceil(total / hpd)
            except:
                pass
        if duration < 1: duration = 1

        # Dátumok
        start_date_obj = t.gantt_start_date if t.gantt_start_date else start
        start_date_str = start_date_obj.strftime("%Y-%m-%d")

        # Szöveg
        txt = t.leiras if t.leiras else (t.master_item.leiras if t.master_item else "-")
        tszam = t.master_item.tetelszam if t.master_item else ""

        data.append({
            'id': t.id,  # Sima ID
            'text': f"{tszam} - {txt[:30]}...",
            'start_date': start_date_str,
            'duration': duration,
            'progress': float(t.progress_percentage) / 100 if t.progress_percentage else 0,
            'parent': f"prj_{t.project.id}",  # <-- EZ RENDELI A PROJEKTHEZ!
            'owner_id': t.alvallalkozo.id if t.alvallalkozo else "",
            'felelos': t.felelos or ""
        })

    # 3. LINKEK
    links = GanttLink.objects.filter(source__project__in=projects)
    link_data = [{'id': l.id, 'source': l.source.id, 'target': l.target.id, 'type': l.type} for l in links]

    return JsonResponse({"data": data, "links": link_data})


@csrf_exempt
def global_gantt_update(request):
    """ Globális mentés kezelő """
    if request.method == 'POST':
        try:
            sid = request.POST.get("id")

            # Ha PROJEKTET próbálnának mozgatni (prj_ prefix), azt ignoráljuk vagy tiltjuk
            if str(sid).startswith("prj_"):
                return JsonResponse({"action": "error", "msg": "A projektet magát nem mozgathatod, csak a feladatait!"})

            # Egyébként hívjuk a sima mentést (DRY elv - Don't Repeat Yourself)
            return gantt_update(request, None)  # A project_id itt nem kell, mert az ID globális

        except Exception as e:
            return JsonResponse({"action": "error", "msg": str(e)})

    return JsonResponse({"action": "error"})

# projects/views.py (A fájl végére add hozzá ezeket)

# === ÚJ MODULOK HELYŐRZŐI ===

def resource_planning(request):
    """ Éves Erőforrás Ütemezés """
    # Itt később a brigádok/alvállalkozók naptárát jelenítjük meg
    return render(request, 'projects/placeholder.html', {'title': 'Éves Erőforrás Ütemezés'})

def hr_dashboard(request):
    """ HR Modul """
    # Itt lesznek a munkavállalók, jelenléti ívek, bérszámfejtési adatok
    return render(request, 'projects/placeholder.html', {'title': 'HR és Munkaügy'})

def global_inventory(request):
    """ Központi Raktárkészlet """
    # Összesítjük az összes projekt készletét
    all_items = ProjectInventory.objects.all().order_by('name')
    return render(request, 'projects/global_inventory.html', {'inventory': all_items})

def finance_dashboard(request):
    """ Pénzügyi Központ """
    # Összesített bevételek és kiadások
    total_expenses = Expense.objects.aggregate(Sum('amount_netto'))['amount_netto__sum'] or 0
    # Később itt lesznek a számlák, áfa kimutatások
    return render(request, 'projects/placeholder.html', {'title': 'Pénzügyi Kimutatások', 'total': total_expenses})


def asset_list(request):
    """ 🚜 Géppark Kezelő (Assets) """
    # Itt lesznek a gépek, szerszámok, lejárati dátumok
    return render(request, 'projects/placeholder.html', {'title': '🚜 Géppark és Eszközök'})

def project_map_view(request):
    """ 🗺️ Térkép Nézet """
    # Itt jelenítjük majd meg a Google Maps / OpenStreetMap térképet
    # Csak az aktív projekteket küldjük majd le
    active_projects = Project.objects.exclude(status__in=['LEZART', 'ELUTASITVA'])
    return render(request, 'projects/placeholder.html', {'title': '🗺️ Projektek Térképen'})

def crm_dashboard(request):
    """ 🤝 CRM / Ügyfélkezelés """
    # Potenciális ügyfelek (Leads) és értékesítési tölcsér
    return render(request, 'projects/placeholder.html', {'title': '🤝 CRM és Értékesítés'})




def uniclass_tree_data(request):
    """
    JSON adatot szolgáltat a JSTree-nek az Uniclass választóhoz.
    """
    # Csak a szükséges mezőket kérjük le a gyorsaság érdekében
    nodes = UniclassNode.objects.all().values('code', 'title_en', 'title_hu', 'parent__code')

    data = []
    for n in nodes:
        # Ha van magyar név, azt írjuk ki, ha nincs, az angolt
        label = n['title_hu'] if n['title_hu'] else n['title_en']

        data.append({
            "id": n['code'],
            "parent": n['parent__code'] if n['parent__code'] else "#",  # '#' jelzi a gyökérelemet a JSTree-ben
            "text": f"{n['code']} - {label}",
            "icon": "fa fa-folder" if not n['parent__code'] else "fa fa-file"  # Ikonok
        })

    return JsonResponse(data, safe=False)


# projects/views.py (A FÁJL VÉGÉRE)

# ... (előző kódok) ...

# === UNICLASS API (EZ HIÁNYZOTT) ===
def uniclass_tree_data(request):
    """
    JSON adatot szolgáltat a JSTree-nek az Uniclass választóhoz.
    """
    # Csak a szükséges mezőket kérjük le a gyorsaság érdekében
    # Ha sok adat van, érdemes lenne lazy loadingot használni, de egyelőre töltsük be mindet
    nodes = UniclassNode.objects.all().values('id', 'code', 'title_en', 'title_hu', 'parent_id')

    data = []
    for n in nodes:
        # Címke: Kód - Név (Magyar ha van, amúgy Angol)
        label = n['title_hu'] if n['title_hu'] else n['title_en']
        text = f"{n['code']} - {label}"

        # JSTree formátum
        data.append({
            "id": str(n['id']),  # Fontos: String ID
            "parent": str(n['parent_id']) if n['parent_id'] else "#",  # '#' jelzi a gyökérelemet
            "text": text,
            "icon": "fa fa-folder" if not n['parent_id'] else "fa fa-tag",
            "a_attr": {"title": text}  # Tooltip
        })

    return JsonResponse(data, safe=False)