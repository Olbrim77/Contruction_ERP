# projects/admin.py
from django.contrib import admin
from .models import Project, Task, Munkanem, Alvallalkozo, Supplier, Material, MasterItem, ItemComponent, Tetelsor, Expense, DailyLog, CompanySettings, CompanySite, Signatory, ProjectDocument, MaterialOrder, OrderItem

class TaskInline(admin.TabularInline): model = Task; extra = 1
class ItemComponentInline(admin.TabularInline): model = ItemComponent; extra = 1
class CompanySiteInline(admin.TabularInline): model = CompanySite; extra = 0; verbose_name = "Telephely"; verbose_name_plural = "További Telephelyek"
class SignatoryInline(admin.TabularInline): model = Signatory; extra = 1; verbose_name = "Aláíró"; verbose_name_plural = "Aláírásra Jogosultak"
class ProjectDocumentInline(admin.TabularInline): model = ProjectDocument; extra = 0; verbose_name = "Dokumentum"; verbose_name_plural = "Csatolt Dokumentumok"

# === ÚJ: RENDELÉS TÉTELEK INLINE ===
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(MaterialOrder)
class MaterialOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'supplier', 'date', 'status')
    list_filter = ('project', 'status', 'date')
    inlines = [OrderItemInline] # Tételek a rendelésen belül

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
    fieldsets = (('Cég Alapadatok', {'fields': ('name', 'tax_number', 'phone', 'email', 'logo')}), ('Székhely Címe', {'fields': (('head_country_code', 'head_zip_code'), ('head_city', 'head_street'), ('head_house_number', 'head_floor', 'head_door'))}))
    def has_add_permission(self, request):
        if CompanySettings.objects.exists(): return False
        return True

admin.site.register(Munkanem)
admin.site.register(Alvallalkozo)
admin.site.register(Supplier)
admin.site.register(Material)
admin.site.register(Expense)
admin.site.register(DailyLog)
admin.site.register(ProjectDocument)