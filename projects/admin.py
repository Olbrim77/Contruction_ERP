# projects/admin.py
from django.contrib import admin
from .models import Project, Task, Munkanem, Alvallalkozo, Supplier, Material, MasterItem, ItemComponent, Tetelsor, Expense, DailyLog, CompanySettings, CompanySite, Signatory, ProjectDocument, MaterialOrder, OrderItem, ProjectInventory, UniclassNode

class TaskInline(admin.TabularInline): model = Task; extra = 1
class ItemComponentInline(admin.TabularInline): model = ItemComponent; extra = 1
class CompanySiteInline(admin.TabularInline): model = CompanySite; extra = 0
class SignatoryInline(admin.TabularInline): model = Signatory; extra = 1
class OrderItemInline(admin.TabularInline): model = OrderItem; extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date')
    inlines = [TaskInline]

@admin.register(MasterItem)
class MasterItemAdmin(admin.ModelAdmin):
    list_display = ('tetelszam', 'leiras', 'egyseg', 'fix_anyag_ar', 'uniclass_item')
    search_fields = ('tetelszam', 'leiras')
    list_filter = ('munkanem', 'uniclass_item')
    inlines = [ItemComponentInline]

@admin.register(UniclassNode)
class UniclassNodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'title_en', 'title_hu', 'table', 'parent')
    search_fields = ('code', 'title_en', 'title_hu')
    list_filter = ('table',)

admin.site.register(Munkanem)
admin.site.register(Alvallalkozo)
admin.site.register(Supplier)
admin.site.register(Material)
admin.site.register(Expense)
admin.site.register(DailyLog)
admin.site.register(ProjectDocument)
admin.site.register(MaterialOrder)
admin.site.register(ProjectInventory)