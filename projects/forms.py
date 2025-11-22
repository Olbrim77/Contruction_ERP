# projects/forms.py
from django import forms
from .models import Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog, Supplier, Material, MasterItem, \
    ItemComponent


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'location', 'client', 'start_date', 'end_date', 'budget', 'hourly_rate', 'vat_rate',
                  'hours_per_day']
        labels = {'name': 'Projekt neve', 'location': 'Helyszín', 'client': 'Ügyfél neve',
                  'start_date': 'Kezdés dátuma', 'end_date': 'Tervezett befejezés', 'budget': 'Költségvetés (Ft)',
                  'hourly_rate': 'Rezsíóabér (Ft/óra)', 'vat_rate': 'ÁFA kulcs (%)',
                  'hours_per_day': 'Tervezett munkaóra / nap'}
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}),
                   'end_date': forms.DateInput(attrs={'type': 'date'})}


class TetelsorQuantityForm(forms.ModelForm):
    class Meta:
        model = Tetelsor
        fields = ['mennyiseg']
        labels = {'mennyiseg': 'Új Mennyiség'}
        widgets = {'mennyiseg': forms.NumberInput(attrs={'step': '0.01'})}


class TetelsorEditForm(forms.ModelForm):
    material = forms.ModelChoiceField(queryset=Material.objects.all(), required=False, label="Központi Anyag (F)")
    munkanem = forms.ModelChoiceField(queryset=Munkanem.objects.all(), required=False, label="Munkanem (M)")
    alvallalkozo = forms.ModelChoiceField(queryset=Alvallalkozo.objects.all(), required=False, label="Alvállalkozó (O)")

    class Meta:
        model = Tetelsor
        fields = [
            'mennyiseg', 'anyag_egysegar', 'material', 'normaido', 'munkanem', 'alvallalkozo',
            'megjegyzes', 'engy_kod', 'k_jelzo', 'cpr_kod', 'progress_percentage', 'labor_split_percentage'
        ]
        labels = {
            'mennyiseg': 'Mennyiség (D)', 'anyag_egysegar': 'Kézi Anyagár (F)', 'megjegyzes': 'Megjegyzés (J)',
            'progress_percentage': 'Készültségi fok (%)', 'labor_split_percentage': 'Saját munka felosztás (%)',
        }
        widgets = {'megjegyzes': forms.Textarea(attrs={'rows': 3})}


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name', 'date', 'category', 'amount_netto', 'invoice_file']
        labels = {'name': 'Számlaszám / Megnevezés', 'date': 'Dátum', 'category': 'Költség típusa',
                  'amount_netto': 'Nettó összeg (Ft)', 'invoice_file': 'Számla feltöltése (Opcionális)'}
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}


class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['date', 'weather', 'workforce', 'work_done', 'problems']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}), 'work_done': forms.Textarea(attrs={'rows': 5}),
                   'problems': forms.Textarea(attrs={'rows': 3})}


class TetelsorCreateFromMasterForm(forms.Form):
    master_item = forms.ModelChoiceField(queryset=MasterItem.objects.all(), label="Válassz tételt a Törzsből")
    mennyiseg = forms.DecimalField(label="Mennyiség", decimal_places=2)


# === EZ A FORM HIÁNYZOTT A HIBÁNÁL ===
class MasterItemForm(forms.ModelForm):
    class Meta:
        model = MasterItem
        fields = ['tetelszam', 'leiras', 'egyseg', 'normaido', 'fix_anyag_ar', 'munkanem', 'engy_kod', 'k_jelzo',
                  'cpr_kod']
        labels = {'tetelszam': 'Tételszám', 'leiras': 'Tétel szövege', 'fix_anyag_ar': 'Alapértelmezett Anyagár (Ft)',
                  'normaido': 'Normaidő'}
        widgets = {'leiras': forms.Textarea(attrs={'rows': 3})}


# === ÉS EZ IS ===
class ItemComponentForm(forms.ModelForm):
    material = forms.ModelChoiceField(queryset=Material.objects.all(), label="Válassz Anyagot")

    class Meta:
        model = ItemComponent
        fields = ['material', 'amount']
        labels = {'amount': 'Szükséges mennyiség (pl. db, kg)'}
        widgets = {'amount': forms.NumberInput(attrs={'step': '0.01'})}