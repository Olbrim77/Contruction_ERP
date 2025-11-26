# projects/admin.py
from django.contrib import admin
from .models import Project, Task, Munkanem, Alvallalkozo, Supplier, Material, MasterItem, ItemComponent, Tetelsor, Expense, DailyLog, CompanySettings, CompanySite, Signatory, ProjectDocument, MaterialOrder, OrderItem, ProjectInventory

class TaskInline(admin.TabularInline): model = Task; extra = 1
class ItemComponentInline(admin.TabularInline): model = ItemComponent; extra = 1
class CompanySiteInline(admin.TabularInline): model = CompanySite; extra = 0
class SignatoryInline(admin.TabularInline): model = Signatory; extra = 1
class ProjectDocumentInline(admin.TabularInline): model = ProjectDocument; extra = 0
class OrderItemInline(admin.TabularInline): model = OrderItem; extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date')
    inlines = [TaskInline, ProjectDocumentInline]

@admin.register(MasterItem)
class MasterItemAdmin(admin.ModelAdmin):
    list_display = ('tetelszam', 'leiras', 'egyseg', 'fix_anyag_ar', 'normaido')
    search_fields = ('tetelszam', 'leiras')
    inlines = [ItemComponentInline]

@admin.register(Tetelsor)
class TetelsorAdmin(admin.ModelAdmin):
    list_display = ('project', 'master_item', 'mennyiseg', 'anyag_osszesen')
    list_filter = ('project',)

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    inlines = [SignatoryInline, CompanySiteInline]
    def has_add_permission(self, request): return not CompanySettings.objects.exists()

@admin.register(MaterialOrder)
class MaterialOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'supplier', 'status', 'date')
    inlines = [OrderItemInline]

admin.site.register(Munkanem)
admin.site.register(Alvallalkozo)
admin.site.register(Supplier)
admin.site.register(Material)
admin.site.register(Expense)
admin.site.register(DailyLog)
admin.site.register(ProjectDocument)
admin.site.register(ProjectInventory)