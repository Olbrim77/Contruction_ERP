from django.db import models
from decimal import Decimal


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

    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projektek"


class Task(models.Model):
    STATUS_CHOICES = [('FUGGO', 'Függőben'), ('FOLYAMATBAN', 'Folyamatban'), ('FELULVIZSG', 'Felülvizsgálat alatt'),
                      ('KESZ', 'Kész'), ]
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE,
                                verbose_name="Kapcsolódó Projekt")
    name = models.CharField(max_length=200, verbose_name="Feladat neve")
    description = models.TextField(verbose_name="Részletes leírás", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FUGGO', verbose_name="Státusz")
    due_date = models.DateField(verbose_name="Határidő", null=True, blank=True)

    def __str__(self): return f"[{self.project.name}] - {self.name}"

    class Meta:
        verbose_name = "Feladat"
        verbose_name_plural = "Feladatok"
        ordering = ['status', 'due_date']


class Munkanem(models.Model):
    nev = models.CharField(max_length=150, unique=True, verbose_name="Munkanem neve")

    def __str__(self): return self.nev

    class Meta: verbose_name, verbose_name_plural = "Munkanem", "Munkanemek"


class Alvallalkozo(models.Model):
    nev = models.CharField(max_length=200, verbose_name="Alvállalkozó neve")
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Kapcsolódó munkanem")

    def __str__(self): return self.nev

    class Meta: verbose_name, verbose_name_plural = "Alvállalkozó", "Alvállalkozók"


class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Beszállító neve")
    contact = models.CharField(max_length=200, blank=True, verbose_name="Kapcsolattartó")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefonszám")
    email = models.EmailField(blank=True)

    def __str__(self): return self.name

    class Meta: verbose_name, verbose_name_plural = "Beszállító", "Beszállítók"


class Material(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Anyag neve/kódja")
    unit = models.CharField(max_length=20, verbose_name="Egység (pl. db, m3, zsák)")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Aktuális egységár (Nettó)")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Fő Beszállító")

    def __str__(self): return f"{self.name} ({self.price} Ft/{self.unit})"

    class Meta: verbose_name, verbose_name_plural = "Anyag", "Anyagok"


class Tetelsor(models.Model):
    project = models.ForeignKey(Project, related_name='tetelsorok', on_delete=models.CASCADE,
                                verbose_name="Kapcsolódó Projekt")
    sorszam = models.CharField(max_length=50, verbose_name="Sorszám", blank=True)
    tetelszam = models.CharField(max_length=100, verbose_name="Tételszám", db_index=True)
    leiras = models.TextField(verbose_name="Leírás (Feladat)")
    mennyiseg = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Mennyiség")
    egyseg = models.CharField(max_length=20, verbose_name="Egység (ME)", blank=True)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Kapcsolódó Anyag")

    labor_split_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00,
                                                 verbose_name="Saját munka felosztás (%)")
    dij_egysegre_sajat = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                             verbose_name="Díj Egységre (Saját)")
    dij_egysegre_alv = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                           verbose_name="Díj Egységre (Alváll.)")
    sajat_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                  verbose_name="Saját Munkadíj Összesen")
    alv_munkadij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                verbose_name="Alvállalkozói Díj Összesen")
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                              verbose_name="Készültségi fok (%)")

    anyag_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Anyag Összesen")
    megjegyzes = models.TextField(verbose_name="Megjegyzés", blank=True, null=True)
    engy_kod = models.CharField(max_length=50, verbose_name="ÉNGY kód", blank=True, null=True)
    k_jelzo = models.CharField(max_length=50, verbose_name="K.jelző", blank=True, null=True)
    munkanem = models.ForeignKey(Munkanem, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Munkanem")
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Normaidő (óra)")
    alvallalkozo = models.ForeignKey(Alvallalkozo, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="Alvállalkozó")
    cpr_kod = models.CharField(max_length=50, verbose_name="CPR kód", blank=True, null=True)

    def save(self, *args, **kwargs):
        rate = self.project.hourly_rate or Decimal(0)
        norma = self.normaido or Decimal(0)
        mennyiseg = self.mennyiseg or Decimal(0)
        split_percent = self.labor_split_percentage / Decimal(100)

        if self.material and self.material.price is not None:
            self.anyag_osszesen = mennyiseg * self.material.price
        else:
            self.anyag_osszesen = Decimal(0)

        full_labor_cost_unit = rate * norma
        self.dij_egysegre_sajat = full_labor_cost_unit * split_percent
        self.dij_egysegre_alv = full_labor_cost_unit * (Decimal(1) - split_percent)
        self.sajat_munkadij_osszesen = mennyiseg * self.dij_egysegre_sajat
        self.alv_munkadij_osszesen = mennyiseg * self.dij_egysegre_alv
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tetelszam} - {self.leiras[:50]}"

    class Meta:
        verbose_name, verbose_name_plural, unique_together = "Tételsor", "Tételsorok", ('project', 'tetelszam')


class Expense(models.Model):
    CATEGORY_CHOICES = [('ANYAG', 'Anyagköltség'), ('MUNKADIJ', 'Munkadíj'), ('EGYEB', 'Egyéb / Általános')]
    project = models.ForeignKey(Project, related_name='expenses', on_delete=models.CASCADE,
                                verbose_name="Kapcsolódó Projekt")
    name = models.CharField(max_length=200, verbose_name="Tétel megnevezése / Számlaszám")
    date = models.DateField(verbose_name="Fizetés/Számla dátuma")
    amount_netto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Nettó összeg (Ft)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='ANYAG', verbose_name="Kategória")
    invoice_file = models.FileField(upload_to='invoices/%Y/%m/', null=True, blank=True, verbose_name="Számla kép/PDF")

    def __str__(self): return f"{self.name} - {self.amount_netto} Ft"

    class Meta: verbose_name, verbose_name_plural, ordering = "Kiadás / Számla", "Kiadások", ['-date']


class DailyLog(models.Model):
    WEATHER_CHOICES = [('NAPOS', 'Napos'), ('FELHOS', 'Felhős'), ('ESOS', 'Esős'), ('HAVAS', 'Havas'),
                       ('SZEL', 'Szeles')]
    project = models.ForeignKey(Project, related_name='daily_logs', on_delete=models.CASCADE, verbose_name="Projekt")
    date = models.DateField(unique=True, verbose_name="Dátum")
    weather = models.CharField(max_length=10, choices=WEATHER_CHOICES, default='NAPOS', verbose_name="Időjárás")
    workforce = models.PositiveIntegerField(verbose_name="Jelenlévő munkaerő (fő)", default=0)
    work_done = models.TextField(verbose_name="Elvégzett munka / Haladás")
    problems = models.TextField(verbose_name="Problémák / Események", blank=True, null=True)

    def __str__(self): return f"Napló: {self.project.name} ({self.date})"

    class Meta: verbose_name, verbose_name_plural, ordering, unique_together = "Napi Jelentés", "Napi Jelentések", [
        '-date'], ('project', 'date')