# projects/models.py
from django.db import models
from decimal import Decimal
from django.utils import timezone


# --- PROJEKT MODELL ---
class Project(models.Model):
    STATUS_CHOICES = [
        ('UJ_KERES', '1. Új Megkeresés (Lead)'),
        ('FELMERES', '2. Felmérés alatt'),
        ('AJANLAT', '3. Ajánlattétel'),
        ('ELOKESZITES', '4. Projekt Előkészítés'),
        ('KIVITELEZES', '5. Kivitelezés (Lebonyolítás)'),
        ('ATADAS', '6. Műszaki Átadás-Átvétel'),
        ('LEZART', '7. Lezárt (Sikeres)'),
        ('ELUTASITVA', '8. Elutasítva / Meghiúsult'),
        ('TORLES_KERELEM', '9. Törlési kérelem alatt'),  # <-- ÚJ (Hivatalos lett)
    ]
    name = models.CharField(max_length=200, verbose_name="Projekt neve")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UJ_KERES', verbose_name="Státusz")
    location = models.CharField(max_length=255, verbose_name="Helyszín")

    contact_name = models.CharField(max_length=150, verbose_name="Megrendelő Neve", blank=True)
    contact_phone = models.CharField(max_length=50, verbose_name="Telefonszám", blank=True)
    contact_email = models.EmailField(verbose_name="Email cím", blank=True)
    contact_address = models.CharField(max_length=255, verbose_name="Számlázási Cím", blank=True)
    client = models.CharField(max_length=150, blank=True, verbose_name="Ügyfél (Régi)")

    # Céges adatok
    is_company = models.BooleanField(default=False, verbose_name="Céges megrendelő?")
    company_name = models.CharField(max_length=200, blank=True, verbose_name="Cégnév (Ha céges)")
    tax_number = models.CharField(max_length=50, blank=True, verbose_name="Adószám")

    inquiry_date = models.DateField(verbose_name="Beérkezés", null=True, blank=True)
    callback_date = models.DateField(verbose_name="Visszahívás", null=True, blank=True)
    survey_date = models.DateField(verbose_name="Felmérés", null=True, blank=True)
    quote_date = models.DateField(verbose_name="Ajánlattétel", null=True, blank=True)
    contract_date = models.DateField(verbose_name="Szerződés", null=True, blank=True)
    start_date = models.DateField(verbose_name="Kezdés", null=True, blank=True)
    handover_date = models.DateField(verbose_name="Átadás", null=True, blank=True)
    end_date = models.DateField(verbose_name="Befejezés", null=True, blank=True)

    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Keret")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=5000, verbose_name="Rezsíóabér")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=27.00, verbose_name="ÁFA %")
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.00, verbose_name="Napi óra")

    def __str__(self): return self.name

    class Meta: verbose_name, verbose_name_plural = "Projekt", "Projektek"


# --- TÖRZSADAT MODELLEK ---
class Munkanem(models.Model):
    nev = models.CharField(max_length=150, unique=True)

    def __str__(self): return self.nev

    class Meta: verbose_name, verbose_name_plural = "Munkanem", "Munkanemek"


class Alvallalkozo(models.Model):
    nev = models.CharField(max_length=200)
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return self.nev

    class Meta: verbose_name, verbose_name_plural = "Alvállalkozó", "Alvállalkozók"


class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Beszállító Neve")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="Kapcsolattartó")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")

    def __str__(self): return self.name

    class Meta: verbose_name, verbose_name_plural = "Beszállító", "Beszállítók"


class Material(models.Model):
    name = models.CharField(max_length=200, unique=True)
    unit = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"{self.name} ({self.price} Ft)"

    class Meta: verbose_name, verbose_name_plural = "Anyag", "Anyagok"


class MasterItem(models.Model):
    tetelszam = models.CharField(max_length=100, unique=True)
    leiras = models.TextField()
    egyseg = models.CharField(max_length=20)
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fix_anyag_ar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)
    engy_kod = models.CharField(max_length=50, blank=True, null=True)
    k_jelzo = models.CharField(max_length=50, blank=True, null=True)
    cpr_kod = models.CharField(max_length=50, blank=True, null=True)

    @property
    def calculated_material_cost(self):
        components = self.components.all()
        if components.exists(): return sum(c.amount * c.material.price for c in components)
        return self.fix_anyag_ar

    def __str__(self): return self.tetelszam

    class Meta: verbose_name, verbose_name_plural = "Törzs Tétel", "Törzs Tételek"


class ItemComponent(models.Model):
    master_item = models.ForeignKey(MasterItem, related_name='components', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


# --- TÉTELSOR ---
class Tetelsor(models.Model):
    project = models.ForeignKey(Project, related_name='tetelsorok', on_delete=models.CASCADE)
    master_item = models.ForeignKey(MasterItem, on_delete=models.PROTECT, verbose_name="Törzs Tétel")
    sorszam = models.CharField(max_length=50, blank=True)
    leiras = models.TextField(verbose_name="Leírás", default="")
    mennyiseg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    egyseg = models.CharField(max_length=20, verbose_name="Egység", default="")
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    anyag_egysegar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    alvallalkozo = models.ForeignKey(Alvallalkozo, on_delete=models.SET_NULL, null=True, blank=True)
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)
    megjegyzes = models.TextField(blank=True, null=True)
    engy_kod = models.CharField(max_length=50, blank=True, null=True)
    k_jelzo = models.CharField(max_length=50, blank=True, null=True)
    cpr_kod = models.CharField(max_length=50, blank=True, null=True)

    labor_split_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    anyag_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dij_egysegre_sajat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dij_egysegre_alv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sajat_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    alv_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if self.master_item and not self.leiras:
            self.leiras = self.master_item.leiras
            self.egyseg = self.master_item.egyseg
            self.normaido = self.master_item.normaido
            self.munkanem = self.master_item.munkanem
            self.engy_kod = self.master_item.engy_kod
            self.k_jelzo = self.master_item.k_jelzo
            self.cpr_kod = self.master_item.cpr_kod
            if not self.anyag_egysegar: self.anyag_egysegar = self.master_item.calculated_material_cost
        if self.material and self.material.price is not None: self.anyag_egysegar = self.material.price
        rate = Decimal(str(self.project.hourly_rate or 0));
        norma = Decimal(str(self.normaido or 0));
        mennyiseg = Decimal(str(self.mennyiseg or 0));
        price = Decimal(str(self.anyag_egysegar or 0));
        split = Decimal(str(self.labor_split_percentage or 100)) / Decimal(100)
        self.anyag_osszesen = mennyiseg * price
        full_labor = rate * norma
        self.dij_egysegre_sajat = full_labor * split;
        self.dij_egysegre_alv = full_labor * (Decimal(1) - split)
        self.sajat_munkadij_osszesen = mennyiseg * self.dij_egysegre_sajat;
        self.alv_munkadij_osszesen = mennyiseg * self.dij_egysegre_alv
        super().save(*args, **kwargs)

    @property
    def tetelszam(self):
        return self.master_item.tetelszam

    def __str__(self):
        return f"{self.master_item.tetelszam}"

    class Meta:
        verbose_name, verbose_name_plural = "Projekt Tétel", "Projekt Tételek"


class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE);
    name = models.CharField(max_length=200);
    status = models.CharField(max_length=20, default='FUGGO');
    due_date = models.DateField(null=True)

    class Meta: verbose_name, verbose_name_plural = "Feladat", "Feladatok"


class Expense(models.Model):
    CATEGORY_CHOICES = [('ANYAG', 'Anyagköltség'), ('MUNKADIJ', 'Munkadíj'), ('EGYEB', 'Egyéb')]
    project = models.ForeignKey(Project, related_name='expenses', on_delete=models.CASCADE);
    name = models.CharField(max_length=200);
    date = models.DateField();
    amount_netto = models.DecimalField(max_digits=12, decimal_places=2);
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='ANYAG');
    invoice_file = models.FileField(upload_to='invoices/', null=True, blank=True)

    class Meta: ordering = ['-date']


# === JAVÍTOTT DAILY LOG (UNIQUE TOGETHER) ===
class DailyLog(models.Model):
    WEATHER_CHOICES = [('NAPOS', 'Napos'), ('FELHOS', 'Felhős'), ('ESOS', 'Esős')]
    project = models.ForeignKey(Project, related_name='daily_logs', on_delete=models.CASCADE)
    date = models.DateField()  # <-- Itt vettük ki a unique=True-t
    weather = models.CharField(max_length=10, choices=WEATHER_CHOICES, default='NAPOS')
    workforce = models.PositiveIntegerField(default=0)
    work_done = models.TextField()
    problems = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('project', 'date')  # <-- Itt tettük be a helyes megszorítást


# === CÉGBEÁLLÍTÁSOK ===
class CompanySettings(models.Model):
    name = models.CharField(max_length=200, verbose_name="Cégnév", default="Saját Építőipari Kft.")
    tax_number = models.CharField(max_length=50, verbose_name="Adószám", blank=True)
    phone = models.CharField(max_length=50, verbose_name="Telefonszám", blank=True)
    email = models.EmailField(verbose_name="Email cím", blank=True)
    logo = models.ImageField(upload_to='company_logo/', verbose_name="Céges Logó", blank=True, null=True)
    head_country_code = models.CharField(max_length=5, default="H", verbose_name="Országkód")
    head_zip_code = models.CharField(max_length=10, verbose_name="Irányítószám", default="")
    head_city = models.CharField(max_length=100, verbose_name="Helység név", default="")
    head_street = models.CharField(max_length=100, verbose_name="Utca név", default="")
    head_house_number = models.CharField(max_length=20, verbose_name="Házszám / HRSZ", default="")
    head_floor = models.CharField(max_length=20, verbose_name="Emelet", blank=True, null=True)
    head_door = models.CharField(max_length=20, verbose_name="Ajtó", blank=True, null=True)

    def full_address(self):
        addr = f"{self.head_country_code}-{self.head_zip_code} {self.head_city}, {self.head_street} {self.head_house_number}."
        if self.head_floor: addr += f" {self.head_floor} em."
        if self.head_door: addr += f" {self.head_door} ajtó"
        return addr

    def __str__(self):
        return "Cégbeállítások (Székhely)"

    class Meta:
        verbose_name = "Cégbeállítások (Székhely)"
        verbose_name_plural = "Cégbeállítások (Székhely)"


class CompanySite(models.Model):
    company = models.ForeignKey(CompanySettings, on_delete=models.CASCADE, related_name='sites')
    site_country_code = models.CharField(max_length=5, default="H", verbose_name="Országkód")
    site_zip_code = models.CharField(max_length=10, verbose_name="Irányítószám")
    site_city = models.CharField(max_length=100, verbose_name="Helység név")
    site_street = models.CharField(max_length=100, verbose_name="Utca név")
    site_house_number = models.CharField(max_length=20, verbose_name="Házszám / HRSZ")
    site_floor = models.CharField(max_length=20, verbose_name="Emelet", blank=True, null=True)
    site_door = models.CharField(max_length=20, verbose_name="Ajtó", blank=True, null=True)

    def __str__(self): return f"Telephely: {self.site_city}, {self.site_street}"

    class Meta:
        verbose_name = "Telephely"
        verbose_name_plural = "Telephelyek"


class Signatory(models.Model):
    company = models.ForeignKey(CompanySettings, on_delete=models.CASCADE, related_name='signatories')
    name = models.CharField(max_length=100, verbose_name="Név")
    position = models.CharField(max_length=100, verbose_name="Beosztás", default="Ügyvezető")

    def __str__(self): return f"{self.name} ({self.position})"

    class Meta: verbose_name, verbose_name_plural = "Aláíró", "Aláírásra Jogosultak"


class ProjectDocument(models.Model):
    CATEGORY_CHOICES = [('TERV', 'Tervrajz'), ('SZERZODES', 'Szerződés'), ('ENGEDELY', 'Hatósági Engedély'),
                        ('FOTO', 'Helyszíni Fotó'), ('FELMERES', 'Felmérési Napló'),
                        ('TELJESITES', 'Teljesítésigazolás'), ('EGYEB', 'Egyéb')]
    project = models.ForeignKey(Project, related_name='documents', on_delete=models.CASCADE)
    file = models.FileField(upload_to='project_docs/%Y/%m/', verbose_name="Fájl")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='EGYEB', verbose_name="Kategória")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Feltöltve")
    description = models.CharField(max_length=255, blank=True, verbose_name="Leírás / Megnevezés")

    def __str__(self): return f"{self.get_category_display()}: {self.description or self.file.name}"

    class Meta: verbose_name, verbose_name_plural = "Dokumentum", "Dokumentumok"


# === ANYAGRENDELÉS ===
class MaterialOrder(models.Model):
    STATUS_CHOICES = [
        ('TERVEZET', 'Tervezet (Szerkesztés alatt)'),
        ('ELKULDVE', 'Elküldve (Várakozás)'),
        ('VISSZAIGAZOLVA', 'Visszaigazolva'),
        ('TELJESITVE', 'Teljesítve / Beérkezett'),
        ('LEMONDVA', 'Lemondva'),
    ]
    project = models.ForeignKey(Project, related_name='material_orders', on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Beszállító")
    date = models.DateField(default=timezone.now, verbose_name="Rendelés dátuma")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TERVEZET', verbose_name="Státusz")
    notes = models.TextField(blank=True, verbose_name="Megjegyzés")

    def __str__(self):
        return f"Rendelés #{self.id} - {self.supplier} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Anyagrendelés"
        verbose_name_plural = "Anyagrendelések"
        ordering = ['-date']


class OrderItem(models.Model):
    order = models.ForeignKey(MaterialOrder, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name="Anyag neve")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Mennyiség")
    unit = models.CharField(max_length=20, verbose_name="Egység")
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Becsült Egységár")

    @property
    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"