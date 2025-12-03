# projects/views_mobile.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Project, Employee, Attendance, PayrollItem, LeaveRequest
from .forms import LeaveRequestForm  # Ne felejtsd el a form importálást!


# --- MOBIL FŐOLDAL ---
@login_required
def mobile_dashboard(request):
    """
    A mobil kezdőlap. Már nem listáz projekteket, csak a menüt.
    """
    return render(request, 'projects/mobile/mobile_dashboard.html')


# --- PROJEKT VÁLASZTÓ (EZ HIÁNYZOTT!) ---
@login_required
def mobile_project_selector(request, action_type):
    """
    Köztes oldal: Itt választja ki a dolgozó a projektet a Naplóhoz vagy Jelenléthez.
    """
    # Csak a futó projektek közül választhat
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


# --- NAPI NAPLÓ (Átirányítás) ---
@login_required
def mobile_daily_log(request, project_id):
    return redirect('daily-log-create', project_id=project_id)


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
        selected_project_id = attendance.project.id
    except Attendance.DoesNotExist:
        attendance = None
        selected_project_id = project_id

    if request.method == 'POST':
        proj_id = request.POST.get('project')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_driver = request.POST.get('is_driver') == 'on'
        is_abroad = request.POST.get('is_abroad') == 'on'
        advance_amount = request.POST.get('advance_amount')
        gps_lat = request.POST.get('gps_lat')
        gps_lon = request.POST.get('gps_lon')

        try:
            fmt = '%H:%M'
            t1 = datetime.strptime(start_time, fmt)
            t2 = datetime.strptime(end_time, fmt)
            delta = t2 - t1
            hours = delta.total_seconds() / 3600
            if hours < 0: hours += 24
        except:
            hours = 8.0

        if not proj_id:
            return redirect('mobile-attendance', project_id=project_id)

        selected_project = get_object_or_404(Project, id=proj_id)

        Attendance.objects.update_or_create(
            employee=employee, date=today,
            defaults={'project': selected_project, 'start_time': start_time, 'end_time': end_time,
                      'hours_worked': round(hours, 1), 'is_driver': is_driver, 'is_abroad': is_abroad,
                      'gps_lat': gps_lat, 'gps_lon': gps_lon}
        )

        if advance_amount:
            try:
                amt = int(advance_amount)
                if amt > 0:
                    PayrollItem.objects.update_or_create(employee=employee, date=today, type='ADVANCE',
                                                         defaults={'amount': amt, 'note': f"Mobilról: {today}",
                                                                   'approved': False})
                    messages.success(request, f"Jelenlét és {amt} Ft előleg rögzítve!")
            except ValueError:
                pass
        else:
            messages.success(request, "Jelenlét sikeresen rögzítve!")

        return redirect('mobile-dashboard')

    return render(request, 'projects/mobile/mobile_attendance.html', {
        'today': today, 'employee': employee, 'attendance': attendance,
        'projects': active_projects, 'selected_project_id': selected_project_id
    })


# --- SZABADSÁG IGÉNYLÉS (EZ IS KELL!) ---
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