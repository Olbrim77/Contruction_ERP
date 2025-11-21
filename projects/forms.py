# projects/forms.py
from django import forms
from .models import Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog, Supplier, Material, MasterItem


class ProjectForm(forms.ModelForm):
    """
    Ez az űrlap a 'Project' modellünkhöz kapcsolódik.
    """

    class Meta:
        model = Project
        fields = [
            'name', 'location', 'client', 'start_date', 'end_date', 'budget',
            'hourly_rate', 'vat_rate', 'hours_per_day',
        ]
        labels = {
            'name': 'Projekt neve', 'location': 'Helyszín', 'client': 'Ügyfél neve',
            'start_date': 'Kezdés dátuma', 'end_date': 'Tervezett befejezés', 'budget': 'Költségvetés (Ft)',
            'hourly_rate': 'Rezsíóabér (Ft/óra)', 'vat_rate': 'ÁFA kulcs (%)',
            'hours_per_day': 'Tervezett munkaóra / nap',
        }
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TetelsorQuantityForm(forms.ModelForm):
    """
    Egy egyszerű űrlap, ami CSAK a tételsor mennyiségét módosítja (gyorsszerkesztés).
    """

    class Meta:
        model = Tetelsor
        fields = ['mennyiseg']
        labels = {'mennyiseg': 'Új Mennyiség'}
        widgets = {'mennyiseg': forms.NumberInput(attrs={'step': '0.01'})}


class TetelsorEditForm(forms.ModelForm):
    """
    Tételsor részletes szerkesztő űrlapja.
    Itt lehet megadni a kézi árat VAGY kiválasztani egy központi anyagot.
    """

    material = forms.ModelChoiceField(
        queryset=Material.objects.all(),
        required=False,
        label="Központi Anyag (Ha kiválasztod, ez felülírja a kézi árat!)"
    )
    munkanem = forms.ModelChoiceField(
        queryset=Munkanem.objects.all(), required=False, label="Munkanem (M)"
    )
    alvallalkozo = forms.ModelChoiceField(
        queryset=Alvallalkozo.objects.all(), required=False, label="Alvállalkozó (O)"
    )

    class Meta:
        model = Tetelsor
        fields = [
            'mennyiseg',  # Mennyiség
            'anyag_egysegar',  # Kézi ár (visszatettük!)
            'material',  # Központi anyag (opcionális)
            'alvallalkozo',  # Alvállalkozó
            'megjegyzes',  # Megjegyzés
            'progress_percentage',  # Készültség
            'labor_split_percentage'  # Munkadíj felosztás
        ]
        labels = {
            'mennyiseg': 'Mennyiség (D)',
            'anyag_egysegar': 'Anyag Egységár (Kézi/Excelből)',
            'megjegyzes': 'Megjegyzés (J)',
            'progress_percentage': 'Készültségi fok (%)',
            'labor_split_percentage': 'Saját munka felosztás (%)',
        }
        widgets = {
            'megjegyzes': forms.Textarea(attrs={'rows': 4}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name', 'date', 'category', 'amount_netto', 'invoice_file']
        labels = {
            'name': 'Számlaszám / Megnevezés', 'date': 'Dátum', 'category': 'Költség típusa',
            'amount_netto': 'Nettó összeg (Ft)', 'invoice_file': 'Számla feltöltése (Opcionális)',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['date', 'weather', 'workforce', 'work_done', 'problems']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'work_done': forms.Textarea(attrs={'rows': 5}),
            'problems': forms.Textarea(attrs={'rows': 3}),
        }


# Import űrlap (nem ModelForm)
class TetelsorCreateFromMasterForm(forms.Form):
    master_item = forms.ModelChoiceField(queryset=MasterItem.objects.all(), label="Válassz tételt a Törzsből")
    mennyiseg = forms.DecimalField(label="Mennyiség", decimal_places=2)