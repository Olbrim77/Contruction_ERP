# projects/forms.py
from django import forms
from .models import Project, Task, Tetelsor, Munkanem, Alvallalkozo


class ProjectForm(forms.ModelForm):
    """
    Ez az űrlap a 'Project' modellünkhöz kapcsolódik.
    """

    class Meta:
        model = Project
        fields = [
            'name',
            'location',
            'client',
            'start_date',
            'end_date',
            'budget',
            'hourly_rate',
            'vat_rate',
            'hours_per_day',
        ]

        labels = {
            'name': 'Projekt neve',
            'location': 'Helyszín',
            'client': 'Ügyfél neve',
            'start_date': 'Kezdés dátuma',
            'end_date': 'Tervezett befejezés',
            'budget': 'Költségvetés (Ft)',
            'hourly_rate': 'Rezsíóabér (Ft/óra)',
            'vat_rate': 'ÁFA kulcs (%)',
            'hours_per_day': 'Tervezett munkaóra / nap',
        }

        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TetelsorQuantityForm(forms.ModelForm):
    """
    Egy egyszerű űrlap, ami CSAK a tételsor mennyiségét módosítja.
    """

    class Meta:
        model = Tetelsor
        fields = ['mennyiseg']
        labels = {
            'mennyiseg': 'Új Mennyiség',
        }
        widgets = {
            'mennyiseg': forms.NumberInput(attrs={'step': '0.01'})
        }


# === EZ A TELJESEN ÚJ ŰRLAP (Kérés 3) ===
class TetelsorEditForm(forms.ModelForm):
    """
    Egy teljes űrlap a tételsor "J"-től "P"-ig tartó mezőinek szerkesztéséhez.
    A 'munkanem' és 'alvallalkozo' mezők mostantól dropdown listák lesznek.
    """

    # Létrehozzuk a dropdown listákat (QuerySet)
    munkanem = forms.ModelChoiceField(
        queryset=Munkanem.objects.all(),
        required=False,  # Engedjük, hogy üres legyen
        label="Munkanem (M)"
    )
    alvallalkozo = forms.ModelChoiceField(
        queryset=Alvallalkozo.objects.all(),
        required=False,  # Engedjük, hogy üres legyen
        label="Alvállalkozó (O)"
    )

    class Meta:
        model = Tetelsor
        fields = [
            'megjegyzes',  # J
            'engy_kod',  # K
            'k_jelzo',  # L
            'munkanem',  # M
            'normaido',  # N
            'alvallalkozo',  # O
            'cpr_kod',  # P
            # Hozzáadjuk ezeket is, mert logikus itt szerkeszteni őket
            'leiras',
            'anyag_egysegar',
        ]
        labels = {
            'megjegyzes': 'Megjegyzés (J)',
            'engy_kod': 'ÉNGY kód (K)',
            'k_jelzo': 'K.jelző (L)',
            'normaido': 'Normaidő (N)',
            'cpr_kod': 'CPR kód (P)',
            'leiras': 'Leírás (C)',
            'anyag_egysegar': 'Anyag Egységár (F)',
        }
        widgets = {
            'megjegyzes': forms.Textarea(attrs={'rows': 4}),
            'leiras': forms.Textarea(attrs={'rows': 4}),
        }