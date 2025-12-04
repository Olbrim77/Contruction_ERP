# projects/admin.py
from django.contrib import admin
from .models import (
    Project,
    Task,
    Munkanem,
    Alvallalkozo,
    Supplier,
    Material,
    MasterItem,
    ItemComponent,
    Tetelsor,
    Expense,
    DailyLog,
    ProjectDocument,
    MaterialOrder,
    OrderItem,
    ProjectInventory,
    UniclassNode,
    Operation,
    Machine,
    LaborComponent,
    MachineComponent,
    Employee,
    Attendance,
    PayrollItem,
    LeaveBalance,
    PublicHoliday,
    AttendanceAuditLog,
)

class TaskInline(admin.TabularInline): model = Task; extra = 1
class ItemComponentInline(admin.TabularInline): model = ItemComponent; extra = 1
class LaborComponentInline(admin.TabularInline): model = LaborComponent; extra = 1
class MachineComponentInline(admin.TabularInline): model = MachineComponent; extra = 1
class OrderItemInline(admin.TabularInline): model = OrderItem; extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date')
    inlines = [TaskInline]

@admin.register(MasterItem)
class MasterItemAdmin(admin.ModelAdmin):
    list_display = ('tetelszam', 'leiras', 'egyseg', 'fix_anyag_ar', 'normaido')
    search_fields = ('tetelszam', 'leiras')
    list_filter = ('munkanem', 'uniclass_item')
    inlines = [ItemComponentInline, LaborComponentInline, MachineComponentInline]

@admin.register(UniclassNode)
class UniclassNodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'title_en', 'table', 'parent')
    search_fields = ('code', 'title_en')
    list_filter = ('table',)

admin.site.register(Munkanem)
admin.site.register(Alvallalkozo)
admin.site.register(Supplier)
admin.site.register(Material)
admin.site.register(Operation)
admin.site.register(Machine)
admin.site.register(Expense)
admin.site.register(DailyLog)
admin.site.register(ProjectDocument)
admin.site.register(MaterialOrder)
admin.site.register(ProjectInventory)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'phone', 'daily_cost', 'status')
    list_filter = ('status', 'position')
    search_fields = ('name',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'employee', 'project', 'hours_worked')
    list_filter = ('date', 'project', 'employee')

@admin.register(PayrollItem)
class PayrollItemAdmin(admin.ModelAdmin):
    list_display = ('date', 'employee', 'type', 'amount', 'approved')
    list_filter = ('type', 'employee', 'approved')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'year', 'total_days')
    list_filter = ('year',)


@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name', 'is_workday')
    ordering = ['date']


@admin.register(AttendanceAuditLog)
class AttendanceAuditLogAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'modified_by', 'modified_at', 'reason')
    readonly_fields = ('attendance', 'modified_by', 'modified_at', 'original_value', 'new_value')

## Removed duplicate admin registrations for Employee, Attendance, and PayrollItem to avoid AlreadyRegistered errors.