# projects/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Project, Task, Tetelsor, Munkanem, Alvallalkozo
# === BŐVÍTETT IMPORT AZ ÚJ ŰRLAPOKKAL ===
from .forms import ProjectForm, TetelsorQuantityForm, TetelsorEditForm

import openpyxl
from django.core.files.storage import default_storage
import os
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum, F

import math
from datetime import timedelta


# --- SEGÉDFÜGGVÉNY (VÁLTOZATLAN) ---
def calculate_work_end_date(start_date, workdays):
    if not start_date or workdays == 0:
        return None
    current_date = start_date
    days_to_add = int(workdays)
    while current_date.weekday() >= 5:
        current_date += timedelta(days=1)
    added_days = 0
    while added_days < days_to_add:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:
            added_days += 1
    return current_date


# --- Lista nézet (VÁLTOZATLAN) ---
def project_list(request):
    projects = Project.objects.exclude(status='TORLES_KERELEM').order_by('start_date')
    context = {'projects_key': projects}
    return render(request, 'projects/project_list.html', context)


# --- Részletező nézet (VÁLTOZATLAN) ---
def project_detail(request, pk):
    project = get_object_or_404(Project, id=pk)
    tasks = project.tetelsorok.all().order_by('sorszam')
    summary = tasks.aggregate(
        total_anyag=Sum('anyag_osszesen'),
        total_dij=Sum('dij_osszesen'),
        total_effort_hours=Sum(F('mennyiseg') * F('normaido'))
    )
    total_anyag = summary.get('total_anyag') or Decimal(0)
    total_dij = summary.get('total_dij') or Decimal(0)
    total_project_netto = total_anyag + total_dij
    vat_rate = project.vat_rate
    total_vat = (total_project_netto * vat_rate) / Decimal(100)
    total_project_brutto = total_project_netto + total_vat
    total_effort_hours = summary.get('total_effort_hours') or Decimal(0)
    hours_per_day = project.hours_per_day
    total_workdays = 0
    if hours_per_day and hours_per_day > 0:
        total_workdays = math.ceil(total_effort_hours / hours_per_day)
    calculated_end_date = calculate_work_end_date(project.start_date, total_workdays)
    context = {
        'project': project,
        'tasks': tasks,
        'total_anyag': total_anyag,
        'total_dij': total_dij,
        'total_project_netto': total_project_netto,
        'vat_rate': vat_rate,
        'total_vat': total_vat,
        'total_project_brutto': total_project_brutto,
        'total_effort_hours': total_effort_hours,
        'total_workdays': total_workdays,
        'calculated_end_date': calculated_end_date
    }
    return render(request, 'projects/project_detail.html', context)


# --- Létrehozó nézet (VÁLTOZATLAN) ---
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


# --- Szerkesztő nézet (VÁLTOZATLAN) ---
def project_update(request, pk):
    project_to_edit = get_object_or_404(Project, id=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project_to_edit)
        if form.is_valid():
            recalculate_dij = False
            if 'hourly_rate' in form.changed_data:
                recalculate_dij = True
                new_rate = form.cleaned_data['hourly_rate']
            form.save()
            if recalculate_dij:
                project_to_edit.tetelsorok.update(
                    dij_egysegre=new_rate * F('normaido')
                )
                project_to_edit.tetelsorok.update(
                    dij_osszesen=F('mennyiseg') * F('dij_egysegre')
                )
            return redirect('project-detail', pk=project_to_edit.id)
    else:
        form = ProjectForm(instance=project_to_edit)
    context = {'form': form}
    return render(request, 'projects/project_form.html', context)


# --- Törlési Kérelem Nézet (VÁLTOZATLAN) ---
def project_request_deletion(request, pk):
    project_to_delete = get_object_or_404(Project, id=pk)
    if request.method == 'POST':
        project_to_delete.status = 'TORLES_KERELEM'
        project_to_delete.save()
        return redirect('project-list')
    context = {'project': project_to_delete}
    return render(request, 'projects/project_confirm_delete.html', context)


# === IMPORT NÉZET (MÓDOSÍTVA: Kérés 1 & 2) ===
def import_tasks(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # === BIZTONSÁGOS CELLA OLVASÓ FUNKCIÓ ===
    def get_cell_value(row, index, default=""):
        # Ez a funkció biztonságosan olvassa a cellát
        # Még akkor is, ha a sor rövidebb, mint az 'index'
        try:
            val = row[index].value
            return str(val) if val is not None else default
        except (IndexError, AttributeError):
            # Ha a sor "csonka" (túl rövid) vagy a cella nem létezik,
            # üres stringet adunk vissza. (Kérés 1)
            return default

    def get_cell_decimal(row, index):
        # Ugyanaz, de számokhoz (Decimal)
        try:
            val = row[index].value
            return Decimal(val) if val is not None else Decimal(0)
        except (IndexError, AttributeError, TypeError, ValueError):
            return Decimal(0)

    # ========================================

    if request.method == 'POST' and 'temp_file_path' in request.POST:
        temp_file_path = request.POST.get('temp_file_path')
        selected_sheets = request.POST.getlist('sheets')
        full_path = os.path.join(settings.MEDIA_ROOT, temp_file_path)

        row_counter = 1  # === Automatikus sorszámozás indítása (Kérés 2) ===

        try:
            workbook = openpyxl.load_workbook(full_path, data_only=True)
            for sheet_name in selected_sheets:
                if sheet_name not in workbook.sheetnames:
                    continue
                ws = workbook[sheet_name]

                for row in ws.iter_rows(min_row=2):
                    if not row or len(row) < 2:
                        continue

                    tetelszam = get_cell_value(row, 1)  # "B" oszlop
                    if not tetelszam:
                        continue

                    # === ADATOK KINYERÉSE (Már a biztonságos funkcióval) ===
                    # "A" oszlopot (row[0]) már nem olvassuk!
                    leiras = get_cell_value(row, 2)  # C
                    mennyiseg = get_cell_decimal(row, 3)  # D
                    egyseg = get_cell_value(row, 4)  # E
                    anyag_egysegar = get_cell_decimal(row, 5)  # F
                    megjegyzes = get_cell_value(row, 9)  # J
                    engy_kod = get_cell_value(row, 10)  # K
                    k_jelzo = get_cell_value(row, 11)  # L
                    normaido = get_cell_decimal(row, 13)  # N
                    cpr_kod = get_cell_value(row, 15)  # P

                    # === KAPCSOLÓDÓ OBJEKTUMOK (M & O) ===
                    munkanem_obj = None
                    munkanem_nev = get_cell_value(row, 12)  # M
                    if munkanem_nev:
                        munkanem_obj, _ = Munkanem.objects.get_or_create(nev=munkanem_nev.strip())

                    alvallalkozo_obj = None
                    alvallalkozo_nev = get_cell_value(row, 14)  # O
                    if alvallalkozo_nev:
                        alvallalkozo_obj, _ = Alvallalkozo.objects.get_or_create(nev=alvallalkozo_nev.strip())

                    # === ADATBÁZIS MŰVELET ===
                    defaults_data = {
                        'sorszam': str(row_counter),  # === Automatikus sorszám (Kérés 2) ===
                        'leiras': leiras,
                        'mennyiseg': mennyiseg,
                        'egyseg': egyseg,
                        'anyag_egysegar': anyag_egysegar,
                        'megjegyzes': megjegyzes,
                        'engy_kod': engy_kod,
                        'k_jelzo': k_jelzo,
                        'normaido': normaido,
                        'cpr_kod': cpr_kod,
                        'munkanem': munkanem_obj,
                        'alvallalkozo': alvallalkozo_obj,
                    }

                    tetelsor_obj, created = Tetelsor.objects.update_or_create(
                        project=project,
                        tetelszam=tetelszam,
                        defaults=defaults_data
                    )

                    row_counter += 1  # === Sorszám növelése (Kérés 2) ===

            workbook.close()
        except Exception as e:
            print(f"Hiba a feldolgozás során: {e}")
        finally:
            if default_storage.exists(temp_file_path):
                default_storage.delete(temp_file_path)
        return redirect('project-detail', pk=project.id)

    # --- 1. LÉPCSŐ (Feltöltés - VÁLTOZATLAN) ---
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        if not excel_file.name.endswith('.xlsx'):
            return redirect('project-detail', pk=project.id)
        temp_file_name = f"temp/{project.id}_{excel_file.name}"
        temp_file_path = default_storage.save(temp_file_name, excel_file)
        full_path = os.path.join(settings.MEDIA_ROOT, temp_file_path)
        try:
            workbook = openpyxl.load_workbook(full_path, read_only=True, data_only=True)
            sheet_names = workbook.sheetnames
            workbook.close()
            context = {
                'project': project, 'sheet_names': sheet_names, 'temp_file_path': temp_file_path,
            }
            return render(request, 'projects/import_step2_select.html', context)
        except Exception as e:
            if default_storage.exists(temp_file_path):
                default_storage.delete(temp_file_path)
            print(f"Hiba az Excel olvasásakor: {e}")
            return redirect('project-detail', pk=project.id)

    context = {'project': project}
    return render(request, 'projects/import_step1_upload.html', context)


# --- Mennyiség Módosító Nézet (VÁLTOZATLAN) ---
def tetelsor_update_quantity(request, pk):
    tetelsor = get_object_or_404(Tetelsor, id=pk)
    if request.method == 'POST':
        form = TetelsorQuantityForm(request.POST, instance=tetelsor)
        if form.is_valid():
            form.save()
            return redirect('project-detail', pk=tetelsor.project.id)
    else:
        form = TetelsorQuantityForm(instance=tetelsor)
    context = {
        'form': form,
        'tetelsor': tetelsor
    }
    return render(request, 'projects/tetelsor_form.html', context)


# === EZ A TELJESEN ÚJ NÉZET A RÉSZLETES SZERKESZTÉSHEZ (Kérés 3) ===
def tetelsor_update(request, pk):
    """
    Nézet egy tételsor részletes módosításához (J-P oszlopok, stb.)
    'pk' a TETELSOR azonosítója.
    """
    tetelsor = get_object_or_404(Tetelsor, id=pk)

    if request.method == 'POST':
        form = TetelsorEditForm(request.POST, instance=tetelsor)
        if form.is_valid():
            form.save()  # A 'save()' metódus (models.py) automatikusan újraszámol!
            return redirect('project-detail', pk=tetelsor.project.id)
    else:
        # GET kérés: Mutassuk az űrlapot a jelenlegi adatokkal
        form = TetelsorEditForm(instance=tetelsor)

    context = {
        'form': form,
        'tetelsor': tetelsor
    }
    return render(request, 'projects/tetelsor_edit_form.html', context)