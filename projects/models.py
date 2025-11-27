# projects/models.py
from django.db import models
from decimal import Decimal
from django.utils import timezone
import math


# --- PROJEKT MODELL ---
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
    contact_phone = models.CharField(max_length=50, blank=True);
    contact_email = models.EmailField(blank=True)
    contact_address = models.CharField(max_length=255, blank=True);
    client = models.CharField(max_length=150, blank=True)
    is_company = models.BooleanField(default=False);
    company_name = models.CharField(max_length=200, blank=True);
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


# --- TÖRZSADATOK ---
class Munkanem(models.Model):
    nev = models.CharField(max_length=150, unique=True)

    def __str__(self): return self.nev


class Alvallalkozo(models.Model):
    nev = models.CharField(max_length=200)
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return self.nev


class Supplier(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self): return self.name


class Material(models.Model):
    name = models.CharField(max_length=200, unique=True);
    unit = models.CharField(max_length=20);
    price = models.DecimalField(max_digits=12, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"{self.name} ({self.price} Ft)"


class MasterItem(models.Model):
    tetelszam = models.CharField(max_length=100, unique=True);
    leiras = models.TextField();
    egyseg = models.CharField(max_length=20)
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0);
    fix_anyag_ar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)
    engy_kod = models.CharField(max_length=50, blank=True, null=True);
    k_jelzo = models.CharField(max_length=50, blank=True, null=True);
    cpr_kod = models.CharField(max_length=50, blank=True, null=True)

    @property
    def calculated_material_cost(self):
        comps = self.components.all();
        return sum(c.amount * c.material.price for c in comps) if comps.exists() else self.fix_anyag_ar

    def __str__(self): return self.tetelszam


class ItemComponent(models.Model):
    master_item = models.ForeignKey(MasterItem, related_name='components', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE);
    amount = models.DecimalField(max_digits=10, decimal_places=2)


# --- TÉTELSOR (OKOS MENTÉSSEL) ---
class Tetelsor(models.Model):
    project = models.ForeignKey(Project, related_name='tetelsorok', on_delete=models.CASCADE)
    master_item = models.ForeignKey(MasterItem, on_delete=models.PROTECT)
    sorszam = models.CharField(max_length=50, blank=True);
    leiras = models.TextField(default="")
    mennyiseg = models.DecimalField(max_digits=10, decimal_places=2, default=0);
    egyseg = models.CharField(max_length=20, default="")
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0);
    anyag_egysegar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    alvallalkozo = models.ForeignKey(Alvallalkozo, on_delete=models.SET_NULL, null=True, blank=True)
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)
    megjegyzes = models.TextField(blank=True, null=True)
    engy_kod = models.CharField(max_length=50, blank=True, null=True);
    k_jelzo = models.CharField(max_length=50, blank=True, null=True);
    cpr_kod = models.CharField(max_length=50, blank=True, null=True)

    labor_split_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    anyag_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dij_egysegre_sajat = models.DecimalField(max_digits=12, decimal_places=2, default=0);
    dij_egysegre_alv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sajat_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0);
    alv_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # GANTT MEZŐK
    gantt_start_date = models.DateField(null=True, blank=True, verbose_name="Tervezett Kezdés")
    gantt_duration = models.IntegerField(default=1, verbose_name="Időtartam (nap)")
    felelos = models.CharField(max_length=100, blank=True, verbose_name="Felelős")

    def save(self, *args, **kwargs):
        # 1. Adatok másolása a törzsből (csak létrehozáskor)
        if self.master_item and not self.leiras:
            self.leiras = self.master_item.leiras;
            self.egyseg = self.master_item.egyseg;
            self.normaido = self.master_item.normaido
            self.munkanem = self.master_item.munkanem;
            self.engy_kod = self.master_item.engy_kod
            self.k_jelzo = self.master_item.k_jelzo;
            self.cpr_kod = self.master_item.cpr_kod
            if not self.anyag_egysegar: self.anyag_egysegar = self.master_item.calculated_material_cost
        if self.material and self.material.price is not None: self.anyag_egysegar = self.material.price

        # 2. Pénzügyi számítások
        rate = Decimal(str(self.project.hourly_rate or 0));
        norma = Decimal(str(self.normaido or 0));
        mennyiseg = Decimal(str(self.mennyiseg or 0))
        price = Decimal(str(self.anyag_egysegar or 0));
        split = Decimal(str(self.labor_split_percentage or 100)) / Decimal(100)
        self.anyag_osszesen = mennyiseg * price;
        full_labor = rate * norma
        self.dij_egysegre_sajat = full_labor * split;
        self.dij_egysegre_alv = full_labor * (Decimal(1) - split)
        self.sajat_munkadij_osszesen = mennyiseg * self.dij_egysegre_sajat;
        self.alv_munkadij_osszesen = mennyiseg * self.dij_egysegre_alv

        # 3. GANTT IDŐTARTAM SZÁMÍTÁS (Ha még nincs kézi érték)
        # Ha az időtartam 1 (alapérték), akkor kiszámoljuk a valósat
        if (not self.gantt_duration or self.gantt_duration <= 1) and norma > 0 and mennyiseg > 0:
            hpd = float(self.project.hours_per_day or 8)
            total_hours = float(mennyiseg * norma)
            if hpd > 0:
                self.gantt_duration = math.ceil(total_hours / hpd)
            if self.gantt_duration < 1: self.gantt_duration = 1

        super().save(*args, **kwargs)

    @property
    def tetelszam(self):
        return self.master_item.tetelszam

    def __str__(self):
        return f"{self.master_item.tetelszam}"


# --- EGYÉB MODELLEK ---
class Task(models.Model):
    STATUS_CHOICES = [('FUGGO', 'Függőben'), ('KESZ', 'Kész')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE);
    name = models.CharField(max_length=200);
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FUGGO');
    due_date = models.DateField(null=True, blank=True)

    class Meta: ordering = ['due_date']


class Expense(models.Model):
    CATEGORY_CHOICES = [('ANYAG', 'Anyag'), ('MUNKADIJ', 'Munkadíj'), ('EGYEB', 'Egyéb')]
    project = models.ForeignKey(Project, related_name='expenses', on_delete=models.CASCADE);
    name = models.CharField(max_length=200)
    date = models.DateField();
    amount_netto = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='ANYAG');
    invoice_file = models.FileField(upload_to='invoices/', null=True, blank=True)

    class Meta: ordering = ['-date']


class DailyLog(models.Model):
    WEATHER_CHOICES = [('NAPOS', 'Napos'), ('FELHOS', 'Felhős'), ('ESOS', 'Esős')]
    project = models.ForeignKey(Project, related_name='daily_logs', on_delete=models.CASCADE)
    date = models.DateField();
    weather = models.CharField(max_length=10, choices=WEATHER_CHOICES, default='NAPOS')
    workforce = models.PositiveIntegerField(default=0);
    work_done = models.TextField();
    problems = models.TextField(blank=True, null=True)

    class Meta: ordering = ['-date']; unique_together = ('project', 'date')


class CompanySettings(models.Model):
    name = models.CharField(max_length=200, default="Saját Kft.");
    tax_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=50, blank=True);
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='company_logo/', blank=True, null=True)
    head_country_code = models.CharField(max_length=5, default="H");
    head_zip_code = models.CharField(max_length=10, default="")
    head_city = models.CharField(max_length=100, default="");
    head_street = models.CharField(max_length=100, default="")
    head_house_number = models.CharField(max_length=20, default="");
    head_floor = models.CharField(max_length=20, blank=True, null=True);
    head_door = models.CharField(max_length=20, blank=True, null=True)

    def full_address(
            self): return f"{self.head_zip_code} {self.head_city}, {self.head_street} {self.head_house_number}."


class CompanySite(models.Model):
    company = models.ForeignKey(CompanySettings, on_delete=models.CASCADE, related_name='sites')
    site_city = models.CharField(max_length=100);
    site_street = models.CharField(max_length=100)
    site_zip_code = models.CharField(max_length=10, default="");
    site_country_code = models.CharField(max_length=5, default="H")
    site_house_number = models.CharField(max_length=20, default="");
    site_floor = models.CharField(max_length=20, blank=True, null=True);
    site_door = models.CharField(max_length=20, blank=True, null=True)


class Signatory(models.Model):
    company = models.ForeignKey(CompanySettings, on_delete=models.CASCADE, related_name='signatories')
    name = models.CharField(max_length=100);
    position = models.CharField(max_length=100, default="Ügyvezető")


class ProjectDocument(models.Model):
    CATEGORY_CHOICES = [('TERV', 'Tervrajz'), ('SZERZODES', 'Szerződés'), ('ENGEDELY', 'Hatósági'), ('FOTO', 'Fotó'),
                        ('FELMERES', 'Felmérés'), ('TELJESITES', 'Teljesítés'), ('EGYEB', 'Egyéb')]
    project = models.ForeignKey(Project, related_name='documents', on_delete=models.CASCADE)
    file = models.FileField(upload_to='project_docs/%Y/%m/');
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='EGYEB')
    uploaded_at = models.DateTimeField(auto_now_add=True);
    description = models.CharField(max_length=255, blank=True)


class MaterialOrder(models.Model):
    STATUS_CHOICES = [('TERVEZET', 'Tervezet'), ('ELKULDVE', 'Elküldve'), ('VISSZAIGAZOLVA', 'Visszaigazolva'),
                      ('TELJESITVE', 'Teljesítve'), ('LEMONDVA', 'Lemondva')]
    project = models.ForeignKey(Project, related_name='material_orders', on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now);
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TERVEZET')
    notes = models.TextField(blank=True)


class OrderItem(models.Model):
    order = models.ForeignKey(MaterialOrder, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200);
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20);
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def total_price(self): return self.quantity * self.price


class ProjectInventory(models.Model):
    project = models.ForeignKey(Project, related_name='inventory', on_delete=models.CASCADE)
    name = models.CharField(max_length=200);
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20);
    last_updated = models.DateTimeField(auto_now=True)

    class Meta: unique_together = ('project', 'name')


class DailyMaterialUsage(models.Model):
    log = models.ForeignKey(DailyLog, related_name='material_usages', on_delete=models.CASCADE)
    inventory_item = models.ForeignKey(ProjectInventory, on_delete=models.CASCADE);
    quantity = models.DecimalField(max_digits=10, decimal_places=2)


class GanttLink(models.Model):
    source = models.ForeignKey(Tetelsor, related_name='source_links', on_delete=models.CASCADE)
    target = models.ForeignKey(Tetelsor, related_name='target_links', on_delete=models.CASCADE)
    type = models.CharField(max_length=2, default='0')