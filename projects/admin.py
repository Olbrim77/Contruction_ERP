# projects/admin.py
from django.contrib import admin
from .models import Project, Task, Munkanem, Alvallalkozo, Supplier, Material, MasterItem, ItemComponent, Tetelsor, Expense, DailyLog

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

class ItemComponentInline(admin.TabularInline):
    model = ItemComponent
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date')
    inlines = [TaskInline]

@admin.register(MasterItem)
class MasterItemAdmin(admin.ModelAdmin):
    # Itt hivatkoztunk a fix_anyag_ar-ra, most már létezik a modellben!
    list_display = ('tetelszam', 'leiras', 'egyseg', 'fix_anyag_ar', 'normaido')
    search_fields = ('tetelszam', 'leiras')
    inlines = [ItemComponentInline]

@admin.register(Tetelsor)
class TetelsorAdmin(admin.ModelAdmin):
    # Itt hivatkoztunk a master_item-re, most már létezik!
    list_display = ('project', 'master_item', 'mennyiseg', 'anyag_osszesen')
    list_filter = ('project',)

admin.site.register(Munkanem)
admin.site.register(Alvallalkozo)
admin.site.register(Supplier)
admin.site.register(Material)
admin.site.register(Expense)
admin.site.register(DailyLog)
admin.site.register(Task)