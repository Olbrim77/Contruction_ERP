# projects/views_mobile.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Project, DailyLog
from .forms import DailyLogForm, DailyMaterialUsageFormSet


# === MOBIL MŰSZERFAL ===
def mobile_dashboard(request):
    """
    Kezdőképernyő: Csak az aktív (folyamatban lévő) projektek listája.
    """
    # Csak a releváns státuszú projekteket mutatjuk a terepen
    active_projects = Project.objects.exclude(
        status__in=['LEZART', 'ELUTASITVA', 'TORLES_KERELEM', 'UJ_KERES']
    ).order_by('name')

    return render(request, 'projects/mobile/dashboard.html', {'projects': active_projects})


# === MOBIL PROJEKT MENÜ ===
def mobile_project_detail(request, pk):
    """
    Egy projekt "főmenüje" mobilon.
    """
    project = get_object_or_404(Project, id=pk)
    today = timezone.localdate()

    # Megnézzük, van-e már mai napló
    todays_log = DailyLog.objects.filter(project=project, date=today).first()

    return render(request, 'projects/mobile/project_detail.html', {
        'project': project,
        'todays_log': todays_log,
        'today': today
    })


# === MOBIL NAPLÓ ÍRÁS ===
def mobile_daily_log(request, project_id):
    """
    Görgethető, egyszerűsített napló űrlap anyagfelhasználással.
    """
    project = get_object_or_404(Project, id=project_id)

    # Megpróbáljuk betölteni a mai naplót, vagy újat kezdünk
    try:
        log_entry = DailyLog.objects.get(project=project, date=timezone.localdate())
    except DailyLog.DoesNotExist:
        log_entry = DailyLog(project=project, date=timezone.localdate())

    if request.method == 'POST':
        form = DailyLogForm(request.POST, instance=log_entry)
        # Fontos: átadjuk a projektet a formset-nek a raktárkészlet szűréséhez!
        formset = DailyMaterialUsageFormSet(request.POST, instance=log_entry, form_kwargs={'project': project})

        if form.is_valid() and formset.is_valid():
            log = form.save(commit=False)
            log.project = project
            log.save()

            # Anyagfelhasználás mentése és készlet csökkentése
            usages = formset.save(commit=False)
            for usage in usages:
                # Ha ez egy új sor (még nincs ID-ja), akkor vonjuk le a készletből
                if not usage.pk and usage.inventory_item:
                    usage.inventory_item.quantity -= usage.quantity
                    usage.inventory_item.save()
                usage.log = log
                usage.save()

            # Törölt sorok kezelése
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "Napló sikeresen mentve!")
            return redirect('mobile-project-detail', pk=project.id)
    else:
        form = DailyLogForm(instance=log_entry)
        formset = DailyMaterialUsageFormSet(instance=log_entry, form_kwargs={'project': project})

    return render(request, 'projects/mobile/daily_log_form.html', {
        'form': form,
        'formset': formset,
        'project': project
    })