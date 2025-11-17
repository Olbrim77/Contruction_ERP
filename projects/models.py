# projects/models.py
from django.db import models


class Project(models.Model):
    """
    Egy építőipari projektet képvisel.
    """

    STATUS_CHOICES = [
        ('TERVEZES', 'Tervezés alatt'),
        ('FOLYAMATBAN', 'Folyamatban'),
        ('BEFEJEZETT', 'Befejezett'),
        ('LEZART', 'Lezárt (Pénzügyileg is)'),
        ('TORLES_KERELEM', 'Törlés Kérelmezve'),
    ]

    name = models.CharField(max_length=200, verbose_name="Projekt neve")
    location = models.CharField(max_length=255, verbose_name="Helyszín (cím)")
    client = models.CharField(max_length=150, verbose_name="Ügyfél neve", blank=True)
    start_date = models.DateField(verbose_name="Kezdés dátuma", null=True, blank=True)
    end_date = models.DateField(verbose_name="Tervezett befejezés", null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='TERVEZES',
        verbose_name="Státusz"
    )
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Költségvetés (Ft)",
        null=True,
        blank=True
    )

    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Rezsíóabér (Ft/óra)",
        default=5000
    )

    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="ÁFA kulcs (%)",
        default=27.00
    )

    hours_per_day = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="Tervezett munkaóra / nap",
        default=8.00
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projektek"


class Task(models.Model):
    STATUS_CHOICES = [
        ('FUGGO', 'Függőben'),
        ('FOLYAMATBAN', 'Folyamatban'),
        ('FELULVIZSG', 'Felülvizsgálat alatt'),
        ('KESZ', 'Kész'),
    ]
    project = models.ForeignKey(
        Project,
        related_name='tasks',
        on_delete=models.CASCADE,
        verbose_name="Kapcsolódó Projekt"
    )
    name = models.CharField(max_length=200, verbose_name="Feladat neve")
    description = models.TextField(verbose_name="Részletes leírás", blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='FUGGO',
        verbose_name="Státusz"
    )
    due_date = models.DateField(verbose_name="Határidő", null=True, blank=True)

    def __str__(self):
        return f"[{self.project.name}] - {self.name}"

    class Meta:
        verbose_name = "Feladat"
        verbose_name_plural = "Feladatok"
        ordering = ['status', 'due_date']


class Munkanem(models.Model):
    nev = models.CharField(max_length=150, unique=True, verbose_name="Munkanem neve")

    def __str__(self):
        return self.nev

    class Meta:
        verbose_name = "Munkanem"
        verbose_name_plural = "Munkanemek"


class Alvallalkozo(models.Model):
    nev = models.CharField(max_length=200, verbose_name="Alvállalkozó neve")
    munkanem = models.ForeignKey(
        Munkanem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kapcsolódó munkanem"
    )

    def __str__(self):
        return self.nev

    class Meta:
        verbose_name = "Alvállalkozó"
        verbose_name_plural = "Alvállalkozók"


class Tetelsor(models.Model):
    project = models.ForeignKey(
        Project,
        related_name='tetelsorok',
        on_delete=models.CASCADE,
        verbose_name="Kapcsolódó Projekt"
    )
    sorszam = models.CharField(max_length=50, verbose_name="Sorszám", blank=True)
    tetelszam = models.CharField(max_length=100, verbose_name="Tételszám", db_index=True)
    leiras = models.TextField(verbose_name="Leírás (Feladat)")
    mennyiseg = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Mennyiség")
    egyseg = models.CharField(max_length=20, verbose_name="Egység (ME)", blank=True)
    anyag_egysegar = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Anyag Egységár")
    dij_egysegre = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Díj Egységre")
    anyag_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Anyag Összesen")
    dij_osszesen = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Díj Összesen")
    megjegyzes = models.TextField(verbose_name="Megjegyzés", blank=True, null=True)
    engy_kod = models.CharField(max_length=50, verbose_name="ÉNGY kód", blank=True, null=True)
    k_jelzo = models.CharField(max_length=50, verbose_name="K.jelző", blank=True, null=True)
    munkanem = models.ForeignKey(
        Munkanem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Munkanem"
    )
    normaido = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Normaidő (óra)")
    alvallalkozo = models.ForeignKey(
        Alvallalkozo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Alvállalkozó"
    )
    cpr_kod = models.CharField(max_length=50, verbose_name="CPR kód", blank=True, null=True)

    # === ITT VOLT A HIBA, MOST JAVÍTVA ===
    def save(self, *args, **kwargs):
        # 1. JAVÍTÁS: 'dij_egysege' -> 'dij_egysegre'
        if self.project.hourly_rate and self.normaido:
            self.dij_egysegre = self.project.hourly_rate * self.normaido

        self.anyag_osszesen = self.mennyiseg * self.anyag_egysegar

        # 2. JAVÍTÁS: 'dij_egysege' -> 'dij_egysegre'
        self.dij_osszesen = self.mennyiseg * self.dij_egysegre

        super().save(*args, **kwargs)  # Hívjuk meg az eredeti mentés funkciót

    def __str__(self):
        return f"{self.tetelszam} - {self.leiras[:50]}"

    class Meta:
        verbose_name = "Tételsor"
        verbose_name_plural = "Tételsorok"
        unique_together = ('project', 'tetelszam')