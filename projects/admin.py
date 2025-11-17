# projects/admin.py
from django.contrib import admin
from .models import Project, Task  # Importáljuk a modelljeinket


# ---
# Ez a rész teszi "széppé" és használhatóvá az admin felületet.
# ---

class TaskInline(admin.TabularInline):
    """
    Ez a 'segéd' osztály teszi lehetővé, hogy a Projekt admin oldalán 
    közvetlenül szerkeszthessük a hozzá tartozó Feladatokat.
    'TabularInline' nézetet használunk a kompaktabb megjelenésért.
    """
    model = Task
    extra = 1  # Alapból 1 üres sort mutat új feladat felvételéhez


@admin.register(Project)  # Ez a "dekorátor" regisztrálja a Project modellt
class ProjectAdmin(admin.ModelAdmin):
    """
    Itt szabjuk testre a 'Projektek' listájának és szerkesztőjének kinézetét.
    """
    # Mely oszlopok jelenjenek meg a projekt listában
    list_display = ('name', 'client', 'location', 'status', 'start_date', 'end_date')

    # Milyen szűrőket tegyünk az oldalsávra
    list_filter = ('status', 'client')

    # Mely mezők alapján működjön a keresés
    search_fields = ('name', 'location', 'client')


    # Ide ágyazzuk be a fenti 'TaskInline' osztályt
    inlines = [TaskInline]


@admin.register(Task)  # Regisztráljuk a Task modellt is
class TaskAdmin(admin.ModelAdmin):
    """
    Itt szabjuk testre a 'Feladatok' listájának kinézetét.
    """
    list_display = ('name', 'project', 'status', 'due_date')
    list_filter = ('status', 'project')
    search_fields = ('name', 'description')