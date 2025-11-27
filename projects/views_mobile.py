# projects/views_mobile.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Project, DailyLog, ProjectDocument
from .forms import DailyLogForm, DailyMaterialUsageFormSet, MobilePhotoForm


# === MOBIL MŰSZERFAL ===
def mobile_dashboard(request):
    active_projects = Project.objects.exclude(
        status__in=['LEZART', 'ELUTASITVA', 'TORLES_KERELEM']
    ).order_by('name')
    return render(request, 'projects/mobile/dashboard.html', {'projects': active_projects})


# === MOBIL PROJEKT MENÜ ===
def mobile_project_detail(request, pk):
    project = get_object_or_404(Project, id=pk)
    today = timezone.localdate()
    todays_log = DailyLog.objects.filter(project=project, date=today).first()
    return render(request, 'projects/mobile/project_detail.html', {
        'project': project, 'todays_log': todays_log, 'today': today
    })


# === MOBIL NAPLÓ ÍRÁS (+ FOTÓZÁS) ===
def mobile_daily_log(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    try:
        log_entry = DailyLog.objects.get(project=project, date=timezone.localdate())
    except DailyLog.DoesNotExist:
        log_entry = DailyLog(project=project, date=timezone.localdate())

    if request.method == 'POST':
        form = DailyLogForm(request.POST, instance=log_entry)
        formset = DailyMaterialUsageFormSet(request.POST, instance=log_entry, form_kwargs={'project': project})

        # FONTOS: request.FILES átadása a fotó űrlapnak!
        photo_form = MobilePhotoForm(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid() and photo_form.is_valid():
            # 1. Napló mentése
            log = form.save(commit=False)
            log.project = project
            log.save()

            # 2. Anyagok mentése
            usages = formset.save(commit=False)
            for usage in usages:
                if not usage.pk and usage.inventory_item:
                    usage.inventory_item.quantity -= usage.quantity
                    usage.inventory_item.save()
                usage.log = log
                usage.save()
            for obj in formset.deleted_objects: obj.delete()

            # 3. FOTÓ MENTÉSE (DOKUMENTUMKÉNT)
            photo = photo_form.cleaned_data.get('image')
            if photo:
                ProjectDocument.objects.create(
                    project=project,
                    file=photo,
                    category='FOTO',  # 'FOTO' kategóriába mentjük
                    description=f"Napló fotó: {log.date}"
                )
                messages.success(request, "Napló és fotó mentve!")
            else:
                messages.success(request, "Napló mentve.")

            return redirect('mobile-project-detail', pk=project.id)
    else:
        form = DailyLogForm(instance=log_entry)
        formset = DailyMaterialUsageFormSet(instance=log_entry, form_kwargs={'project': project})
        photo_form = MobilePhotoForm()

    return render(request, 'projects/mobile/daily_log_form.html', {
        'form': form,
        'formset': formset,
        'photo_form': photo_form,
        'project': project
    })