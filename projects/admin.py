from django.contrib import admin
from .models import Project, Task, Munkanem, Alvallalkozo, Tetelsor, Expense, DailyLog, Supplier, Material

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'location', 'status', 'start_date', 'end_date', 'hourly_rate', 'vat_rate')
    list_filter = ('status', 'client')
    search_fields = ('name', 'location', 'client')
    inlines = [TaskInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'status', 'due_date')
    list_filter = ('status', 'project')
    search_fields = ('name', 'description')

admin.site.register(Munkanem)
admin.site.register(Alvallalkozo)
admin.site.register(Supplier)
admin.site.register(Material)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'date', 'amount_netto', 'category')
    list_filter = ('project', 'category', 'date')
    date_hierarchy = 'date'

@admin.register(Tetelsor)
class TetelsorAdmin(admin.ModelAdmin):
    list_display = ('tetelszam', 'leiras', 'project', 'mennyiseg', 'material', 'anyag_osszesen', 'sajat_munkadij_osszesen', 'alv_munkadij_osszesen', 'progress_percentage')
    list_filter = ('project', 'munkanem', 'alvallalkozo')
    search_fields = ('tetelszam', 'leiras')

@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('project', 'date', 'workforce', 'weather')
    list_filter = ('project', 'weather', 'workforce')
    date_hierarchy = 'date'