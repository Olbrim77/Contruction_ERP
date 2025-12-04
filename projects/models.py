# projects/models.py

from django.db import models
from decimal import Decimal
import math
from django.utils import timezone
from django.contrib.auth.models import User


# --- 1. PROJEKT ÉS STRUKTÚRA ---

class Project(models.Model):
    STATUS_CHOICES = [
        ('UJ_KERES', '1. Új Megkeresés (Lead)'), ('FELMERES', '2. Felmérés alatt'), ('AJANLAT', '3. Ajánlattétel'),
        ('ELOKESZITES', '4. Projekt Előkészítés'), ('KIVITELEZES', '5. Kivitelezés'), ('ATADAS', '6. Átadás'),
        ('LEZART', '7. Lezárt'), ('ELUTASITVA', '8. Elutasítva'), ('TORLES_KERELEM', '9. Törlésre vár')
    ]
    name = models.CharField(max_length=200, verbose_name="Projekt neve")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UJ_KERES', verbose_name="Státusz")
    location = models.CharField(max_length=255, verbose_name="Helyszín")

    contact_name = models.CharField(max_length=150, verbose_name="Megrendelő Neve", blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_address = models.CharField(max_length=255, blank=True)
    client = models.CharField(max_length=150, blank=True)
    is_company = models.BooleanField(default=False)
    company_name = models.CharField(max_length=200, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)

    inquiry_date = models.DateField(null=True, blank=True);
    callback_date = models.DateField(null=True, blank=True)
    survey_date = models.DateField(null=True, blank=True);
    quote_date = models.DateField(null=True, blank=True)
    contract_date = models.DateField(null=True, blank=True);
    start_date = models.DateField(null=True, blank=True)
    handover_date = models.DateField(null=True, blank=True);
    end_date = models.DateField(null=True, blank=True)

    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=27.00)
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)

    def __str__(self): return self.name

    class Meta: verbose_name = "Projekt"; verbose_name_plural = "Projektek"


class ProjectChapter(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='chapters')
    name = models.CharField(max_length=200, verbose_name="Fejezet neve")
    rank = models.IntegerField(default=0, verbose_name="Sorrend")

    def __str__(self): return f"{self.name}"

    class Meta: ordering = ['rank']


# --- 2. UNICLASS ÉS TÖRZSADATOK ---

class UniclassNode(models.Model):
    code = models.CharField(max_length=20, unique=True);
    title_en = models.CharField(max_length=255);
    title_hu = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True);
    version = models.CharField(max_length=20, blank=True);
    date = models.CharField(max_length=20, blank=True);
    extra_data = models.TextField(blank=True)
    table = models.CharField(max_length=10);
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self): return f"{self.code} - {self.title_hu or self.title_en}"

    class Meta: ordering = ['code']


class Munkanem(models.Model):
    nev = models.CharField(max_length=150, unique=True)

    def __str__(self): return self.nev


class Alvallalkozo(models.Model):
    nev = models.CharField(max_length=200);
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return self.nev


class Supplier(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self): return self.name


# --- 3. ERŐFORRÁSOK ---

class Material(models.Model):
    name = models.CharField(max_length=200, unique=True);
    unit = models.CharField(max_length=20);
    price = models.DecimalField(max_digits=12, decimal_places=2);
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True);
    uniclass_link = models.ForeignKey(UniclassNode, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"{self.name} ({self.price} Ft)"


class Operation(models.Model):
    name = models.CharField(max_length=200);
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2);
    uniclass_link = models.ForeignKey(UniclassNode, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"{self.name} ({self.hourly_rate} Ft/ó)"


class Machine(models.Model):
    name = models.CharField(max_length=200);
    unit = models.CharField(max_length=20, default="óra");
    price = models.DecimalField(max_digits=12, decimal_places=2);
    uniclass_link = models.ForeignKey(UniclassNode, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"{self.name} ({self.price} Ft)"


# --- 4. RECEPTÚRA ---

class MasterItem(models.Model):
    tetelszam = models.CharField(max_length=100, unique=True);
    leiras = models.TextField();
    egyseg = models.CharField(max_length=20)
    fix_anyag_ar = models.DecimalField(max_digits=12, decimal_places=2, default=0);
    fix_munkadij = models.DecimalField(max_digits=12, decimal_places=2, default=0);
    fix_gep_ar = models.DecimalField(max_digits=12, decimal_places=2, default=0);
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True);
    uniclass_item = models.ForeignKey(UniclassNode, on_delete=models.SET_NULL, null=True, blank=True)
    engy_kod = models.CharField(max_length=50, blank=True);
    k_jelzo = models.CharField(max_length=50, blank=True);
    cpr_kod = models.CharField(max_length=50, blank=True)

    def calculate_totals(self):
        self.fix_anyag_ar = sum(c.amount * c.material.price for c in self.material_components.all())
        self.fix_munkadij = sum(c.time_required * c.operation.hourly_rate for c in self.labor_components.all())
        self.normaido = sum(c.time_required for c in self.labor_components.all())
        self.fix_gep_ar = sum(c.amount * c.machine.price for c in self.machine_components.all())
        self.save()

    @property
    def total_price(self): return self.fix_anyag_ar + self.fix_munkadij + self.fix_gep_ar

    @property
    def calculated_material_cost(self): return self.fix_anyag_ar

    def __str__(self): return self.tetelszam

    class Meta: verbose_name = "Törzs Tétel"; verbose_name_plural = "Törzs Tételek"


class ItemComponent(models.Model): master_item = models.ForeignKey(MasterItem, related_name='material_components',
                                                                   on_delete=models.CASCADE); material = models.ForeignKey(
    Material, on_delete=models.CASCADE); amount = models.DecimalField(max_digits=10, decimal_places=2)


class LaborComponent(models.Model): master_item = models.ForeignKey(MasterItem, related_name='labor_components',
                                                                    on_delete=models.CASCADE); operation = models.ForeignKey(
    Operation, on_delete=models.CASCADE); time_required = models.DecimalField(max_digits=10, decimal_places=2)


class MachineComponent(models.Model): master_item = models.ForeignKey(MasterItem, related_name='machine_components',
                                                                      on_delete=models.CASCADE); machine = models.ForeignKey(
    Machine, on_delete=models.CASCADE); amount = models.DecimalField(max_digits=10, decimal_places=2)


# --- 5. KÖLTSÉGVETÉS ---

class Tetelsor(models.Model):
    project = models.ForeignKey(Project, related_name='tetelsorok', on_delete=models.CASCADE)
    chapter = models.ForeignKey(ProjectChapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks',
                                verbose_name="Fejezet")
    master_item = models.ForeignKey(MasterItem, on_delete=models.PROTECT)
    sorszam = models.CharField(max_length=50, blank=True);
    leiras = models.TextField(default="")
    mennyiseg = models.DecimalField(max_digits=10, decimal_places=2, default=0);
    egyseg = models.CharField(max_length=20, default="")
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0);
    anyag_egysegar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True);
    alvallalkozo = models.ForeignKey(Alvallalkozo, on_delete=models.SET_NULL, null=True, blank=True);
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)
    megjegyzes = models.TextField(blank=True, null=True);
    engy_kod = models.CharField(max_length=50, blank=True);
    k_jelzo = models.CharField(max_length=50, blank=True);
    cpr_kod = models.CharField(max_length=50, blank=True)
    labor_split_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00);
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    anyag_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dij_egysegre_sajat = models.DecimalField(max_digits=12, decimal_places=2, default=0);
    dij_egysegre_alv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sajat_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0);
    alv_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gantt_start_date = models.DateField(null=True, blank=True);
    gantt_duration = models.IntegerField(default=1);
    felelos = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if self.master_item and not self.leiras:
            self.leiras = self.master_item.leiras;
            self.egyseg = self.master_item.egyseg;
            self.normaido = self.master_item.normaido;
            self.munkanem = self.master_item.munkanem;
            self.engy_kod = self.master_item.engy_kod;
            self.k_jelzo = self.master_item.k_jelzo;
            self.cpr_kod = self.master_item.cpr_kod
            if not self.anyag_egysegar: self.anyag_egysegar = self.master_item.calculated_material_cost
        if self.material and self.material.price is not None: self.anyag_egysegar = self.material.price
        rate = Decimal(str(self.project.hourly_rate or 0));
        norma = Decimal(str(self.normaido or 0));
        mennyiseg = Decimal(str(self.mennyiseg or 0));
        price = Decimal(str(self.anyag_egysegar or 0));
        split = Decimal(str(self.labor_split_percentage or 100)) / Decimal(100)
        self.anyag_osszesen = mennyiseg * price;
        full_labor = rate * norma
        self.dij_egysegre_sajat = full_labor * split;
        self.dij_egysegre_alv = full_labor * (Decimal(1) - split)
        self.sajat_munkadij_osszesen = mennyiseg * self.dij_egysegre_sajat;
        self.alv_munkadij_osszesen = mennyiseg * self.dij_egysegre_alv
        if (not self.gantt_duration or self.gantt_duration <= 1) and norma > 0 and mennyiseg > 0:
            hpd = float(self.project.hours_per_day or 8);
            total_hours = float(mennyiseg * norma)
            if hpd > 0: self.gantt_duration = math.ceil(total_hours / hpd)
            if self.gantt_duration < 1: self.gantt_duration = 1
        super().save(*args, **kwargs)

    @property
    def tetelszam(self):
        return self.master_item.tetelszam

    def __str__(self):
        return f"{self.master_item.tetelszam}"


# --- 6. PÉNZÜGY ÉS NAPLÓ ---

class Task(models.Model): project = models.ForeignKey(Project, on_delete=models.CASCADE); name = models.CharField(
    max_length=200); status = models.CharField(max_length=20, default='FUGGO'); due_date = models.DateField(null=True,
                                                                                                            blank=True)


class Meta: ordering = ['due_date']


class Expense(models.Model):
    CATEGORY_CHOICES = [('ANYAG', 'Anyag'), ('MUNKADIJ', 'Munkadíj'), ('EGYEB', 'Egyéb')]
    project = models.ForeignKey(Project, related_name='expenses', on_delete=models.CASCADE)
    name = models.CharField(max_length=200);
    date = models.DateField();
    amount_netto = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='ANYAG')
    invoice_file = models.FileField(upload_to='invoices/', null=True, blank=True)

    class Meta: ordering = ['-date']


class DailyLog(models.Model):
    WEATHER_CHOICES = [('NAPOS', 'Napos'), ('FELHOS', 'Felhős'), ('ESOS', 'Esős')]
    project = models.ForeignKey(Project, related_name='daily_logs', on_delete=models.CASCADE)
    date = models.DateField();
    weather = models.CharField(max_length=10, choices=WEATHER_CHOICES, default='NAPOS')
    workforce = models.PositiveIntegerField(default=0);
    work_done = models.TextField();
    problems = models.TextField(blank=True)

    class Meta: ordering = ['-date']; unique_together = ('project', 'date')


class DailyLogImage(models.Model): log = models.ForeignKey(DailyLog, related_name='images',
                                                           on_delete=models.CASCADE); image = models.ImageField(
    upload_to='daily_logs/%Y/%m/'); uploaded_at = models.DateTimeField(auto_now_add=True)


class ProjectDocument(models.Model): project = models.ForeignKey(Project, related_name='documents',
                                                                 on_delete=models.CASCADE); file = models.FileField(
    upload_to='project_docs/%Y/%m/'); category = models.CharField(max_length=20,
                                                                  default='EGYEB'); uploaded_at = models.DateTimeField(
    auto_now_add=True); description = models.CharField(max_length=255, blank=True)


class MaterialOrder(models.Model): project = models.ForeignKey(Project, related_name='material_orders',
                                                               on_delete=models.CASCADE); supplier = models.ForeignKey(
    Supplier, on_delete=models.SET_NULL, null=True, blank=True); date = models.DateField(
    default=timezone.now); status = models.CharField(max_length=20, default='TERVEZET'); notes = models.TextField(
    blank=True)


class OrderItem(models.Model): order = models.ForeignKey(MaterialOrder, related_name='items',
                                                         on_delete=models.CASCADE); name = models.CharField(
    max_length=200); quantity = models.DecimalField(max_digits=10, decimal_places=2); unit = models.CharField(
    max_length=20); price = models.DecimalField(max_digits=12, decimal_places=2, default=0)


@property
def total_price(self): return self.quantity * self.price


class ProjectInventory(models.Model): project = models.ForeignKey(Project, related_name='inventory',
                                                                  on_delete=models.CASCADE); name = models.CharField(
    max_length=200); quantity = models.DecimalField(max_digits=10, decimal_places=2,
                                                    default=0); unit = models.CharField(
    max_length=20); last_updated = models.DateTimeField(auto_now=True)


class Meta: unique_together = ('project', 'name')


class DailyMaterialUsage(models.Model): log = models.ForeignKey(DailyLog, related_name='material_usages',
                                                                on_delete=models.CASCADE); inventory_item = models.ForeignKey(
    ProjectInventory, on_delete=models.CASCADE); quantity = models.DecimalField(max_digits=10, decimal_places=2)


class GanttLink(models.Model): source = models.ForeignKey(Tetelsor, related_name='source_links',
                                                          on_delete=models.CASCADE); target = models.ForeignKey(
    Tetelsor, related_name='target_links', on_delete=models.CASCADE); type = models.CharField(max_length=2, default='0')


def __str__(self): return f"{self.source} -> {self.target}"


# --- 7. HR ÉS MUNKAERŐ MODUL ---
class Employee(models.Model):
    STATUS_CHOICES = [('ACTIVE', 'Aktív'), ('INACTIVE', 'Inaktív')]
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="Felhasználói Fiók")
    name = models.CharField(max_length=100, verbose_name="Név")
    position = models.CharField(max_length=100, verbose_name="Pozíció")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    daily_cost = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Napi Bérköltség (Ft)")
    tax_id = models.CharField(max_length=50, blank=True, verbose_name="Adóazonosító")
    address = models.CharField(max_length=255, blank=True, verbose_name="Lakcím")
    registration_form = models.FileField(upload_to='hr_docs/', blank=True, null=True, verbose_name="Bejelentő lap")
    contract_file = models.FileField(upload_to='hr_docs/', blank=True, null=True, verbose_name="Munkaszerződés")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name="Státusz")
    joined_date = models.DateField(null=True, blank=True, verbose_name="Belépés dátuma")

    def __str__(self): return self.name

    class Meta: verbose_name = "Dolgozó"; verbose_name_plural = "Dolgozók"


class LeaveBalance(models.Model):
    """ ÉVES SZABADSÁG EGYENLEG """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    year = models.IntegerField(default=timezone.now().year, verbose_name="Év")

    base_leave = models.IntegerField(default=20, verbose_name="Alapszabadság")
    age_leave = models.IntegerField(default=0, verbose_name="Életkor utáni pótszab.")
    child_leave = models.IntegerField(default=0, verbose_name="Gyermek utáni pótszab.")
    carry_over = models.IntegerField(default=0, verbose_name="Tavalyról áthozott")

    def total_days(self):
        return self.base_leave + self.age_leave + self.child_leave + self.carry_over

    def __str__(self): return f"{self.employee.name} - {self.year} ({self.total_days()} nap)"

    class Meta: unique_together = ('employee', 'year'); verbose_name = "Szabadság Egyenleg"


class PublicHoliday(models.Model):
    """ ÜNNEPNAPOK ÉS MUNKANAP ÁTHELYEZÉSEK """
    date = models.DateField(unique=True, verbose_name="Dátum")
    name = models.CharField(max_length=100, verbose_name="Ünnep neve (pl. Karácsony)")
    is_workday = models.BooleanField(default=False, verbose_name="Munkanap? (Szombati ledolgozás)")

    def __str__(self): return f"{self.date} - {self.name}"

    class Meta: verbose_name = "Ünnepnap / Munkarend"; ordering = ['date']


class Attendance(models.Model):
    # --- STÁTUSZOK (A HTML űrlap alapján) ---
    STATUS_CHOICES = [
        ('WORK', '✅ Munkavégzés történt'),
        ('WEATHER', '🌧️ Időjárás miatt állás'),
        ('SICK', '🤒 Betegszabadság'),
        ('ABSENCE', '🚨 Rendkívüli távollét'),
        ('OTHER', '❓ Egyéb ok'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Dolgozó")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Munkaterület", null=True,
                                blank=True)  # Nullable, mert betegség esetén nincs projekt
    date = models.DateField(default=timezone.now, verbose_name="Dátum")

    # Státusz mező
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='WORK', verbose_name="Tevékenység")

    # Munka adatok (Csak WORK esetén)
    start_time = models.TimeField(null=True, blank=True, verbose_name="Kezdés")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Befejezés")
    hours_worked = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="Ledolgozott óra")

    # Pótlékok
    is_driver = models.BooleanField(default=False, verbose_name="Sofőr")
    is_abroad = models.BooleanField(default=False, verbose_name="Külföld")

    # GPS
    gps_lat = models.CharField(max_length=50, blank=True, null=True)
    gps_lon = models.CharField(max_length=50, blank=True, null=True)

    # Igazolás (Csak SICK esetén)
    sick_paper = models.FileField(upload_to='sick_papers/%Y/', blank=True, null=True, verbose_name="Orvosi igazolás")

    # Megjegyzés (ABSENCE/OTHER esetén kötelező)
    note = models.TextField(blank=True, verbose_name="Megjegyzés")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Jelenlét";
        verbose_name_plural = "Jelenléti Ívek";
        ordering = ['-date']
        unique_together = ('employee', 'date')

class AttendanceAuditLog(models.Model):
    """ AUDIT NAPLÓ: KI, MIKOR, MIT MÓDOSÍTOTT? """
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='audit_logs')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Módosító")
    modified_at = models.DateTimeField(auto_now_add=True, verbose_name="Időpont")

    original_value = models.TextField(verbose_name="Eredeti érték")
    new_value = models.TextField(verbose_name="Új érték")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Módosítás oka")

    def __str__(self): return f"{self.attendance} módosítva ekkor: {self.modified_at}"


class PayrollItem(models.Model):
    # ... (Ez marad változatlan a korábbiakból) ...
    TYPE_CHOICES = [('ADVANCE', '💰 Előleg'), ('PREMIUM', '🏆 Prémium'), ('DEDUCTION', '🔻 Levonás'),
                    ('VACATION', '🏖️ Szabadság kifizetés'), ('SICK_LEAVE', '🤒 Táppénz kieg.')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Dolgozó")
    date = models.DateField(default=timezone.now, verbose_name="Dátum")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Típus")
    amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Összeg (Ft)")
    note = models.TextField(blank=True, verbose_name="Megjegyzés")
    approved = models.BooleanField(default=False, verbose_name="Jóváhagyva")

    def __str__(self): return f"{self.employee.name} - {self.get_type_display()}"

    class Meta: verbose_name = "Bér Tétel"; verbose_name_plural = "Bér Tételek"; ordering = ['-date']




# --- CÉGADATOK (EZT PÓTOLTUK!) ---
class CompanySettings(models.Model):
    name = models.CharField(max_length=200, default="Saját Kft.");
    tax_number = models.CharField(max_length=50, blank=True);
    phone = models.CharField(max_length=50, blank=True);
    email = models.EmailField(blank=True);
    logo = models.ImageField(upload_to='company_logo/', blank=True, null=True)
    head_country_code = models.CharField(max_length=5, default="H");
    head_zip_code = models.CharField(max_length=10, default="");
    head_city = models.CharField(max_length=100, default="");
    head_street = models.CharField(max_length=100, default="");
    head_house_number = models.CharField(max_length=20, default="");
    head_floor = models.CharField(max_length=20, blank=True, null=True);
    head_door = models.CharField(max_length=20, blank=True, null=True)

    def full_address(
            self): return f"{self.head_zip_code} {self.head_city}, {self.head_street} {self.head_house_number}."


class CompanySite(models.Model): company = models.ForeignKey(CompanySettings, on_delete=models.CASCADE,
                                                             related_name='sites'); site_city = models.CharField(
    max_length=100); site_street = models.CharField(max_length=100); site_zip_code = models.CharField(max_length=10,
                                                                                                      default=""); site_country_code = models.CharField(
    max_length=5, default="H"); site_house_number = models.CharField(max_length=20,
                                                                     default=""); site_floor = models.CharField(
    max_length=20, blank=True, null=True); site_door = models.CharField(max_length=20, blank=True, null=True)


class Signatory(models.Model): company = models.ForeignKey(CompanySettings, on_delete=models.CASCADE,
                                                           related_name='signatories'); name = models.CharField(
    max_length=100); position = models.CharField(max_length=100, default="Ügyvezető")


# projects/models.py

# ... (a fájl vége) ...

class LeaveRequest(models.Model):
    """ SZABADSÁG IGÉNYLÉSEK """
    STATUS_CHOICES = [
        ('PENDING', '⏳ Függőben'),
        ('APPROVED', '✅ Elfogadva'),
        ('REJECTED', '❌ Elutasítva'),
    ]

    LEAVE_TYPES = [
        ('SZ', 'Fizetett Szabadság'),
        ('B', 'Betegszabadság'),
        ('F', 'Fizetés nélküli'),
        ('TP', 'Tanulmányi'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Dolgozó")
    start_date = models.DateField(verbose_name="Kezdete")
    end_date = models.DateField(verbose_name="Vége")
    leave_type = models.CharField(max_length=5, choices=LEAVE_TYPES, default='SZ', verbose_name="Típus")
    reason = models.TextField(blank=True, verbose_name="Indoklás")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="Státusz")
    proof_file = models.FileField(upload_to='leave_proofs/%Y/', blank=True, null=True,
                                  verbose_name="Igazolás (Fotó/PDF)")
    rejection_reason = models.TextField(blank=True, verbose_name="Elutasítás oka")  # Ha nem engedik

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.employee.name}: {self.start_date} - {self.end_date} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Szabadság Kérelem"
        verbose_name_plural = "Szabadság Kérelmek"

    # --- 8. ANYAG ÉS ESZKÖZ IGÉNYLÉS (Napi Naplóhoz) ---




class LogRequest(models.Model):
    """ A napi naplóban leadott igénylések """

    # JAVÍTOTT LISTA:
    TYPE_CHOICES = [
        ('ANYAG', '🧱 Anyag'),
        ('ESZKOZ', '🔨 Eszköz / Gép'),
        ('SZAKIPAR', '👷 Szakipar'),
        ('SUPPORT', '📐 Műszaki támogatás'),
    ]

    STATUS_CHOICES = [
        ('PENDING', '⏳ Függőben'),
        ('ORDERED', '🛒 Megrendelve'),
        ('DELIVERED', '✅ Szállítva / Teljesítve'),
        ('REJECTED', '❌ Elutasítva'),
    ]

    daily_log = models.ForeignKey('DailyLog', on_delete=models.CASCADE, related_name='requests', verbose_name="Napló")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='ANYAG', verbose_name="Típus")

    # A "név" mezőben fogjuk tárolni a teljes szöveget (pl. "10 zsák cement")
    name = models.CharField(max_length=200, verbose_name="Igény leírása")

    # Ezeket megtartjuk az adatbázis integritás miatt, de üresen maradhatnak
    quantity = models.CharField(max_length=50, blank=True, verbose_name="Mennyiség")
    description = models.TextField(blank=True, verbose_name="Részletes leírás")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="Státusz")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.get_type_display()}: {self.name}"

    class Meta: verbose_name = "Igénylés"; verbose_name_plural = "Igénylések"


# --- 9. HIERARCHIKUS TERVTÁR (Doksi fülhöz) ---


class PlanCategory(models.Model):
    """Mappák a terveknek (pl. Kivitelezési tervek -> Építészet)"""
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='plan_categories')
    name = models.CharField(max_length=100, verbose_name="Mappa neve")
    # Önmagára hivatkozik, így lehetnek almappák!
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='subcategories', verbose_name="Szülő mappa")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Terv Mappa"
        verbose_name_plural = "Terv Mappák"


class PlanDocument(models.Model):
    """Maguk a fájlok a mappákban"""
    category = models.ForeignKey(PlanCategory, on_delete=models.CASCADE, related_name='files', verbose_name="Mappa")
    name = models.CharField(max_length=200, verbose_name="Dokumentum neve")
    file = models.FileField(upload_to='plans/%Y/%m/', verbose_name="Fájl")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Segédfüggvény a kiterjesztéshez (ikonozáshoz)
    @property
    def extension(self):
        import os
        name, ext = os.path.splitext(self.file.name)
        return ext.lower()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tervrajz"
        verbose_name_plural = "Tervrajzok"