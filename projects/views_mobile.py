# projects/views_mobile.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Project, Employee, Attendance, PayrollItem


@login_required
def mobile_dashboard(request):
    # Csak azokat a projekteket mutatjuk, amik futnak
    projects = Project.objects.exclude(status__in=['LEZART', 'ELUTASITVA']).order_by('name')
    return render(request, 'projects/mobile/mobile_dashboard.html', {'projects': projects})


@login_required
def mobile_project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/mobile/mobile_project_detail.html', {'project': project})


@login_required
def mobile_daily_log(request, project_id):
    return redirect('daily-log-create', project_id=project_id)


# --- ÚJ: EGYÉNI JELENLÉTI ÍV ---
@login_required
def mobile_attendance(request, project_id=None):
    """
    A dolgozó saját magának rögzíti a jelenlétét.
    Ha a project_id meg van adva, azt választja ki alapból, de a listából választhat mást is.
    """
    today = timezone.now().date()

    # 1. Keressük meg a bejelentkezett dolgozót
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, "A fiókodhoz nincs Dolgozó profil csatolva! Kérd a rendszergazdát.")
        return redirect('mobile-dashboard')

    # 2. Aktív projektek a legördülőhöz
    active_projects = Project.objects.exclude(status__in=['LEZART', 'ELUTASITVA']).order_by('name')

    # 3. Megnézzük, van-e már mára rögzítve adata
    try:
        attendance = Attendance.objects.get(employee=employee, date=today)
        selected_project_id = attendance.project.id
    except Attendance.DoesNotExist:
        attendance = None
        selected_project_id = project_id  # Ha linkről jött, ez lesz az alapértelmezett

    if request.method == 'POST':
        proj_id = request.POST.get('project')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_driver = request.POST.get('is_driver') == 'on'
        is_abroad = request.POST.get('is_abroad') == 'on'
        advance_amount = request.POST.get('advance_amount')
        gps_lat = request.POST.get('gps_lat')
        gps_lon = request.POST.get('gps_lon')

        # Óraszámítás (Egyszerűsítve: Vége - Kezdés)
        # Formátum: "07:00" -> datetime
        fmt = '%H:%M'
        t1 = datetime.strptime(start_time, fmt)
        t2 = datetime.strptime(end_time, fmt)
        delta = t2 - t1
        hours = delta.total_seconds() / 3600
        if hours < 0: hours += 24  # Ha éjfélen átnyúlik

        # Mentés vagy Frissítés
        selected_project = get_object_or_404(Project, id=proj_id)

        att, created = Attendance.objects.update_or_create(
            employee=employee,
            date=today,
            defaults={
                'project': selected_project,
                'start_time': start_time,
                'end_time': end_time,
                'hours_worked': round(hours, 1),
                'is_driver': is_driver,
                'is_abroad': is_abroad,
                'gps_lat': gps_lat,
                'gps_lon': gps_lon
            }
        )

        # Előleg kezelése (Külön táblába!)
        if advance_amount and int(advance_amount) > 0:
            PayrollItem.objects.create(
                employee=employee,
                date=today,
                type='ADVANCE',
                amount=advance_amount,
                note=f"Mobilról igényelve ({today})"
            )
            messages.success(request, f"Jelenlét és {advance_amount} Ft előleg rögzítve!")
        else:
            messages.success(request, "Jelenlét sikeresen rögzítve!")

        return redirect('mobile-dashboard')

    return render(request, 'projects/mobile/mobile_attendance.html', {
        'today': today,
        'employee': employee,
        'attendance': attendance,  # Ha már van, betöltjük az adatait
        'projects': active_projects,
        'selected_project_id': selected_project_id
    })