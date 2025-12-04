# projects/views_mobile.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import json

# --- MODELLEK IMPORTÁLÁSA (MINDEN, AMI KELL) ---
from .models import (
    Project, Employee, Attendance, PayrollItem, LeaveRequest,
    DailyLog, DailyLogImage, LogRequest, PlanCategory,
    Alvallalkozo, ProjectDocument
)
from .forms import LeaveRequestForm


# --- MOBIL FŐOLDAL ---
@login_required
def mobile_dashboard(request):
    """
    A mobil kezdőlap menüje.
    """
    return render(request, 'projects/mobile/mobile_dashboard.html')


# --- PROJEKT VÁLASZTÓ ---
@login_required
def mobile_project_selector(request, action_type):
    """
    Köztes oldal: Itt választja ki a dolgozó a projektet.
    """
    projects = Project.objects.exclude(status__in=['LEZART', 'ELUTASITVA']).order_by('name')

    return render(request, 'projects/mobile/mobile_project_selector.html', {
        'projects': projects,
        'action_type': action_type
    })


# --- PROJEKT MENÜ ---
@login_required
def mobile_project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/mobile/mobile_project_detail.html', {'project': project})


# --- NAPI NAPLÓ (MOBIL) ---
@login_required
def mobile_daily_log(request, project_id):
    """
    A Napi Napló mobil nézete (Fülekkel, Tervtárral, Igényléssel).
    """
    project = get_object_or_404(Project, id=project_id)
    today = timezone.now().date()

    # 1. Adatok lekérése a legördülőkhöz
    employees = Employee.objects.filter(status='ACTIVE').order_by('name')
    subcontractors = Alvallalkozo.objects.all().order_by('nev')

    # 2. Tervtár lekérése
    root_folders = PlanCategory.objects.filter(
        project=project,
        parent__isnull=True
    ).prefetch_related('files', 'subcategories__files')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # A) Napi Napló Alapadatok
                log, created = DailyLog.objects.update_or_create(
                    project=project,
                    date=request.POST.get('date') or today,
                    defaults={
                        'weather': request.POST.get('weather', 'NAPOS'),
                        'work_done': request.POST.get('work_done', ''),
                        'problems': request.POST.get('problems', ''),
                    }
                )

                # B) Fotók mentése
                images = request.FILES.getlist('images')
                for img in images:
                    DailyLogImage.objects.create(log=log, image=img)

                # C) IGÉNYLÉSEK MENTÉSE (JSON-ból)
                requests_json = request.POST.get('requests_json')
                if requests_json:
                    req_list = json.loads(requests_json)
                    for item in req_list:
                        requests_json = request.POST.get('requests_json')
                        if requests_json:
                            req_list = json.loads(requests_json)
                            for item in req_list:
                                LogRequest.objects.create(
                                    daily_log=log,
                                    type=item.get('type'),
                                    name=item.get('text'),  # A 'text' kulcsot használjuk a frontendről
                                    quantity="",  # Üresen hagyjuk
                                    description="",  # Üresen hagyjuk
                                    status='PENDING'
                                )

                # D) Dokumentumok mentése
                docs = request.FILES.getlist('documents')
                for d in docs:
                    ProjectDocument.objects.create(
                        project=project,
                        file=d,
                        category='EGYEB',
                        description=f"Naplóból feltöltve: {log.date}"
                    )

            messages.success(request, "✅ Napló és Igénylések sikeresen rögzítve!")
            return redirect('mobile-project-detail', pk=project.id)

        except Exception as e:
            messages.error(request, f"Hiba történt a mentéskor: {e}")

    return render(request, 'projects/mobile/daily_log_form.html', {
        'project': project,
        'today': today,
        'employees': employees,
        'subcontractors': subcontractors,
        'root_folders': root_folders,
    })


# --- JELENLÉTI ÍV ---
@login_required
def mobile_attendance(request, project_id=None):
    today = timezone.now().date()

    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, "Nincs dolgozó profilod!")
        return redirect('mobile-dashboard')

    active_projects = Project.objects.exclude(status__in=['LEZART', 'ELUTASITVA']).order_by('name')

    try:
        attendance = Attendance.objects.get(employee=employee, date=today)
        selected_project_id = attendance.project.id if attendance.project else project_id
    except Attendance.DoesNotExist:
        attendance = None
        selected_project_id = project_id

    if request.method == 'POST':
        # Alapadatok
        status = request.POST.get('status')
        note = request.POST.get('note')
        gps_lat = request.POST.get('gps_lat')
        gps_lon = request.POST.get('gps_lon')

        # Munka adatok (csak ha WORK)
        proj_id = request.POST.get('project')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_driver = request.POST.get('is_driver') == 'on'
        is_abroad = request.POST.get('is_abroad') == 'on'
        advance_amount = request.POST.get('advance_amount')

        # Projekt keresése (ha van)
        selected_project = None
        if proj_id:
            selected_project = get_object_or_404(Project, id=proj_id)

        # Óraszámítás
        hours = 0
        if status == 'WORK' and start_time and end_time:
            try:
                fmt = '%H:%M'
                t1 = datetime.strptime(start_time, fmt)
                t2 = datetime.strptime(end_time, fmt)
                delta = t2 - t1
                hours = delta.total_seconds() / 3600
                if hours < 0: hours += 24
            except:
                hours = 0

        # Mentés
        att_obj, created = Attendance.objects.update_or_create(
            employee=employee, date=today,
            defaults={
                'status': status,
                'project': selected_project,
                'start_time': start_time,
                'end_time': end_time,
                'hours_worked': round(hours, 1),
                'is_driver': is_driver,
                'is_abroad': is_abroad,
                'note': note,
                'gps_lat': gps_lat,
                'gps_lon': gps_lon
            }
        )

        # Fájl feltöltés (Betegpapír)
        if status == 'SICK' and request.FILES.get('sick_file'):
            att_obj.sick_paper = request.FILES['sick_file']
            att_obj.save()

        # Előleg kezelése
        if status == 'WORK' and advance_amount:
            try:
                amt = int(advance_amount)
                if amt > 0:
                    PayrollItem.objects.update_or_create(
                        employee=employee, date=today, type='ADVANCE',
                        defaults={'amount': amt, 'note': f"Mobilról: {today}", 'approved': False}
                    )
            except ValueError:
                pass

        messages.success(request, "✅ Jelenlét sikeresen rögzítve!")
        return redirect('mobile-dashboard')

    return render(request, 'projects/mobile/mobile_attendance.html', {
        'today': today, 'employee': employee, 'attendance': attendance,
        'projects': active_projects, 'selected_project_id': selected_project_id
    })


# --- SZABADSÁG IGÉNYLÉS ---
@login_required
def mobile_leave_list(request):
    try:
        employee = request.user.employee
    except Exception:
        return redirect('mobile-dashboard')

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            req = form.save(commit=False)
            req.employee = employee
            if req.end_date < req.start_date:
                messages.error(request, "Hibás dátum!")
            else:
                req.save()
                messages.success(request, "Kérelem elküldve!")
                return redirect('mobile-leave-list')
    else:
        form = LeaveRequestForm(initial={'start_date': timezone.now().date(), 'end_date': timezone.now().date()})

    my_requests = LeaveRequest.objects.filter(employee=employee)
    return render(request, 'projects/mobile/mobile_leave_list.html',
                  {'form': form, 'my_requests': my_requests, 'employee': employee})