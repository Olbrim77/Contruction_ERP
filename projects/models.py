# projects/models.py
from django.db import models
from decimal import Decimal  # Fontos import


class Project(models.Model):
    STATUS_CHOICES = [
        ('TERVEZES', 'Tervezés alatt'), ('FOLYAMATBAN', 'Folyamatban'), ('BEFEJEZETT', 'Befejezett'),
        ('LEZART', 'Lezárt (Pénzügyileg is)'), ('TORLES_KERELEM', 'Törlés Kérelmezve'),
    ]
    name = models.CharField(max_length=200, verbose_name="Projekt neve")
    location = models.CharField(max_length=255, verbose_name="Helyszín (cím)")
    client = models.CharField(max_length=150, verbose_name="Ügyfél neve", blank=True)
    start_date = models.DateField(verbose_name="Kezdés dátuma", null=True, blank=True)
    end_date = models.DateField(verbose_name="Tervezett befejezés", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TERVEZES', verbose_name="Státusz")
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Költségvetés (Ft)", null=True,
                                 blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Rezsíóabér (Ft/óra)", default=5000)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="ÁFA kulcs (%)", default=27.00)
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Tervezett munkaóra / nap",
                                        default=8.00)

    def __str__(self): return self.name

    class Meta: verbose_name, verbose_name_plural = "Projekt", "Projektek"


class Task(models.Model):
    STATUS_CHOICES = [('FUGGO', 'Függőben'), ('KESZ', 'Kész')]
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    name = models.CharField(max_length=200);
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FUGGO');
    due_date = models.DateField(null=True)

    class Meta: verbose_name, verbose_name_plural = "Feladat", "Feladatok"


class Munkanem(models.Model):
    nev = models.CharField(max_length=150, unique=True);

    def __str__(self): return self.nev

    class Meta: verbose_name, verbose_name_plural = "Munkanem", "Munkanemek"


class Alvallalkozo(models.Model):
    nev = models.CharField(max_length=200);
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return self.nev

    class Meta: verbose_name, verbose_name_plural = "Alvállalkozó", "Alvállalkozók"


class Supplier(models.Model):
    name = models.CharField(max_length=200);

    def __str__(self): return self.name

    class Meta: verbose_name, verbose_name_plural = "Beszállító", "Beszállítók"


class Material(models.Model):
    name = models.CharField(max_length=200, unique=True);
    unit = models.CharField(max_length=20);
    price = models.DecimalField(max_digits=12, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"{self.name} ({self.price} Ft)"

    class Meta: verbose_name, verbose_name_plural = "Anyag", "Anyagok"


class MasterItem(models.Model):
    tetelszam = models.CharField(max_length=100, unique=True, verbose_name="Tételszám")
    leiras = models.TextField(verbose_name="Leírás")
    egyseg = models.CharField(max_length=20, verbose_name="Egység")
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Normaidő")
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True)
    fix_anyag_ar = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Fix Anyagár")
    engy_kod = models.CharField(max_length=50, blank=True, null=True)
    k_jelzo = models.CharField(max_length=50, blank=True, null=True)
    cpr_kod = models.CharField(max_length=50, blank=True, null=True)

    @property
    def calculated_material_cost(self):
        components = self.components.all()
        if components.exists(): return sum(c.amount * c.material.price for c in components)
        return self.fix_anyag_ar

    def __str__(self): return f"{self.tetelszam}"

    class Meta: verbose_name, verbose_name_plural = "Törzs Tétel", "Törzs Tételek"


class ItemComponent(models.Model):
    master_item = models.ForeignKey(MasterItem, related_name='components', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE);
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class Tetelsor(models.Model):
    project = models.ForeignKey(Project, related_name='tetelsorok', on_delete=models.CASCADE)
    master_item = models.ForeignKey(MasterItem, on_delete=models.PROTECT, verbose_name="Törzs Tétel")

    sorszam = models.CharField(max_length=50, blank=True)
    mennyiseg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alvallalkozo = models.ForeignKey(Alvallalkozo, on_delete=models.SET_NULL, null=True, blank=True)
    megjegyzes = models.TextField(blank=True, null=True)

    # Kézi felülbírálások
    anyag_egysegar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)

    labor_split_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Számított mezők
    anyag_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dij_egysegre_sajat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dij_egysegre_alv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sajat_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    alv_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # === JAVÍTÁS: Kényszerített Decimal konverzió a hiba elkerülésére ===
        rate = Decimal(str(self.project.hourly_rate or 0))
        norma = Decimal(str(self.master_item.normaido or 0))
        mennyiseg = Decimal(str(self.mennyiseg or 0))
        split_percent = Decimal(str(self.labor_split_percentage or 100)) / Decimal(100)

        # Anyagár logika
        if self.material and self.material.price is not None:
            self.anyag_egysegar = self.material.price
        elif not self.anyag_egysegar:  # Ha 0 vagy None
            self.anyag_egysegar = self.master_item.calculated_material_cost or Decimal(0)

        # Biztosítjuk, hogy az anyag_egysegar is Decimal legyen
        price = Decimal(str(self.anyag_egysegar or 0))
        self.anyag_osszesen = mennyiseg * price

        # Munkadíj számítás
        full_labor_unit = rate * norma
        self.dij_egysegre_sajat = full_labor_unit * split_percent
        self.dij_egysegre_alv = full_labor_unit * (Decimal(1) - split_percent)
        self.sajat_munkadij_osszesen = mennyiseg * self.dij_egysegre_sajat
        self.alv_munkadij_osszesen = mennyiseg * self.dij_egysegre_alv
        super().save(*args, **kwargs)

    # Proxy property-k
    @property
    def tetelszam(self):
        return self.master_item.tetelszam

    @property
    def leiras(self):
        return self.master_item.leiras

    @property
    def egyseg(self):
        return self.master_item.egyseg

    @property
    def munkanem(self):
        return self.master_item.munkanem

    @property
    def normaido(self):
        return self.master_item.normaido

    @property
    def engy_kod(self):
        return self.master_item.engy_kod

    @property
    def k_jelzo(self):
        return self.master_item.k_jelzo

    @property
    def cpr_kod(self):
        return self.master_item.cpr_kod

    def __str__(self):
        return f"{self.master_item.tetelszam}"

    class Meta:
        verbose_name, verbose_name_plural, unique_together = "Projekt Tétel", "Projekt Tételek", (
        'project', 'master_item')


class Expense(models.Model):
    CATEGORY_CHOICES = [('ANYAG', 'Anyagköltség'), ('MUNKADIJ', 'Munkadíj'), ('EGYEB', 'Egyéb')]
    project = models.ForeignKey(Project, related_name='expenses', on_delete=models.CASCADE);
    name = models.CharField(max_length=200);
    date = models.DateField();
    amount_netto = models.DecimalField(max_digits=12, decimal_places=2);
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='ANYAG');
    invoice_file = models.FileField(upload_to='invoices/', null=True, blank=True)

    class Meta: ordering = ['-date']


class DailyLog(models.Model):
    WEATHER_CHOICES = [('NAPOS', 'Napos'), ('FELHOS', 'Felhős'), ('ESOS', 'Esős')]
    project = models.ForeignKey(Project, related_name='daily_logs', on_delete=models.CASCADE);
    date = models.DateField(unique=True);
    weather = models.CharField(max_length=10, choices=WEATHER_CHOICES, default='NAPOS', verbose_name="Időjárás");
    workforce = models.PositiveIntegerField(default=0);
    work_done = models.TextField();
    problems = models.TextField(blank=True, null=True, verbose_name="Problémák")

    class Meta: ordering = ['-date']