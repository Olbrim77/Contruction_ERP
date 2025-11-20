from django import forms
from .models import Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog, Supplier, Material

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'location', 'client', 'start_date', 'end_date', 'budget', 'hourly_rate', 'vat_rate', 'hours_per_day']
        labels = {'name': 'Projekt neve', 'location': 'Helyszín', 'client': 'Ügyfél neve', 'start_date': 'Kezdés dátuma', 'end_date': 'Tervezett befejezés', 'budget': 'Költségvetés (Ft)', 'hourly_rate': 'Rezsíóabér (Ft/óra)', 'vat_rate': 'ÁFA kulcs (%)', 'hours_per_day': 'Tervezett munkaóra / nap'}
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'})}

class TetelsorQuantityForm(forms.ModelForm):
    class Meta:
        model = Tetelsor
        fields = ['mennyiseg']
        labels = {'mennyiseg': 'Új Mennyiség'}
        widgets = {'mennyiseg': forms.NumberInput(attrs={'step': '0.01'})}

class TetelsorEditForm(forms.ModelForm):
    material = forms.ModelChoiceField(queryset=Material.objects.all(), required=False, label="Kapcsolódó anyag (F)")
    munkanem = forms.ModelChoiceField(queryset=Munkanem.objects.all(), required=False, label="Munkanem (M)")
    alvallalkozo = forms.ModelChoiceField(queryset=Alvallalkozo.objects.all(), required=False, label="Alvállalkozó (O)")
    class Meta:
        model = Tetelsor
        fields = ['megjegyzes', 'engy_kod', 'k_jelzo', 'munkanem', 'normaido', 'alvallalkozo', 'cpr_kod', 'leiras', 'material', 'progress_percentage', 'labor_split_percentage']
        labels = {'megjegyzes': 'Megjegyzés (J)', 'engy_kod': 'ÉNGY kód (K)', 'k_jelzo': 'K.jelző (L)', 'normaido': 'Normaidő (N)', 'cpr_kod': 'CPR kód (P)', 'leiras': 'Leírás (C)', 'material': 'Kapcsolódó anyag (F)', 'progress_percentage': 'Készültségi fok (%)', 'labor_split_percentage': 'Saját munka felosztás (%)'}
        widgets = {'megjegyzes': forms.Textarea(attrs={'rows': 4}), 'leiras': forms.Textarea(attrs={'rows': 4})}

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name', 'date', 'category', 'amount_netto', 'invoice_file']
        labels = {'name': 'Számlaszám / Megnevezés', 'date': 'Dátum', 'category': 'Költség típusa', 'amount_netto': 'Nettó összeg (Ft)', 'invoice_file': 'Számla feltöltése (Opcionális)'}
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['date', 'weather', 'workforce', 'work_done', 'problems']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}), 'work_done': forms.Textarea(attrs={'rows': 5}), 'problems': forms.Textarea(attrs={'rows': 3})}