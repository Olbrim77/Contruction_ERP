# projects/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog,
    Supplier, Material, MasterItem, ItemComponent, ProjectDocument,
    MaterialOrder, OrderItem, ProjectInventory, DailyMaterialUsage
)


# --- DÁTUM MEZŐ JAVÍTÁSA IOS-HEZ ---
class DateInput(forms.DateInput):
    input_type = 'date'
    # Ez a formátum kell, hogy az iPhone felismerje az értéket:
    format = '%Y-%m-%d'


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name', 'location', 'client', 'status',
            'is_company', 'company_name', 'tax_number',
            'contact_name', 'contact_phone', 'contact_email', 'contact_address',
            'inquiry_date', 'callback_date', 'survey_date', 'quote_date', 'contract_date',
            'start_date', 'handover_date', 'end_date',
            'budget', 'hourly_rate', 'vat_rate', 'hours_per_day'
        ]
        # Itt használjuk a saját DateInput osztályunkat
        widgets = {
            'inquiry_date': DateInput(),
            'callback_date': DateInput(),
            'survey_date': DateInput(),
            'quote_date': DateInput(),
            'contract_date': DateInput(),
            'start_date': DateInput(),
            'handover_date': DateInput(),
            'end_date': DateInput()
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['project', 'name', 'due_date']
        widgets = {'due_date': DateInput()}  # JAVÍTVA


class TetelsorQuantityForm(forms.ModelForm):
    class Meta: model = Tetelsor; fields = ['mennyiseg']; widgets = {
        'mennyiseg': forms.NumberInput(attrs={'step': '0.01'})}


class TetelsorEditForm(forms.ModelForm):
    material = forms.ModelChoiceField(queryset=Material.objects.all(), required=False, label="Központi Anyag (F)")
    munkanem = forms.ModelChoiceField(queryset=Munkanem.objects.all(), required=False, label="Munkanem (M)")
    alvallalkozo = forms.ModelChoiceField(queryset=Alvallalkozo.objects.all(), required=False, label="Alvállalkozó (O)")

    class Meta:
        model = Tetelsor
        fields = ['mennyiseg', 'leiras', 'egyseg', 'normaido', 'anyag_egysegar', 'material', 'alvallalkozo', 'munkanem',
                  'megjegyzes', 'engy_kod', 'k_jelzo', 'cpr_kod', 'progress_percentage', 'labor_split_percentage']
        widgets = {'megjegyzes': forms.Textarea(attrs={'rows': 3}), 'leiras': forms.Textarea(attrs={'rows': 3})}


class ExpenseForm(forms.ModelForm):
    class Meta: model = Expense; fields = ['name', 'date', 'category', 'amount_netto', 'invoice_file'];

    widgets = {'date': DateInput()}  # JAVÍTVA


class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['date', 'weather', 'workforce', 'work_done', 'problems']
        widgets = {
            'date': DateInput(),  # JAVÍTVA (Ez a legfontosabb a mobil naplóhoz!)
            'work_done': forms.Textarea(attrs={'rows': 5}),
            'problems': forms.Textarea(attrs={'rows': 3})
        }


class TetelsorCreateFromMasterForm(forms.Form):
    master_item = forms.ModelChoiceField(queryset=MasterItem.objects.all(), label="Válassz tételt a Törzsből")
    mennyiseg = forms.DecimalField(label="Mennyiség", decimal_places=2)


class MasterItemForm(forms.ModelForm):
    class Meta: model = MasterItem; fields = '__all__'; widgets = {'leiras': forms.Textarea(attrs={'rows': 3})}


class ItemComponentForm(forms.ModelForm):
    class Meta: model = ItemComponent; fields = ['material', 'amount']; widgets = {
        'amount': forms.NumberInput(attrs={'step': '0.01'})}


class ProjectDocumentForm(forms.ModelForm):
    class Meta:
        model = ProjectDocument
        fields = ['category', 'file', 'description']
        labels = {
            'category': 'Dokumentum Típusa',
            'file': 'Fájl kiválasztása',
            'description': 'Rövid leírás / Megnevezés (Opcionális)'
        }


class MaterialOrderForm(forms.ModelForm):
    class Meta:
        model = MaterialOrder
        fields = ['supplier', 'date', 'status', 'notes']
        widgets = {
            'date': DateInput(),  # JAVÍTVA
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


OrderItemFormSet = inlineformset_factory(
    MaterialOrder, OrderItem,
    fields=['name', 'quantity', 'unit', 'price'],
    extra=1,
    can_delete=True
)


# FOTÓZÁSHOZ (Ez jó volt, de hagyjuk meg)
class MobilePhotoForm(forms.Form):
    image = forms.ImageField(
        label="📷 Fotó készítése",
        required=False,
        widget=forms.ClearableFileInput(attrs={'capture': 'environment', 'accept': 'image/*', 'class': 'photo-input'})
    )


class DailyMaterialUsageForm(forms.ModelForm):
    class Meta:
        model = DailyMaterialUsage
        fields = ['inventory_item', 'quantity']

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['inventory_item'].queryset = ProjectInventory.objects.filter(project=project)


DailyMaterialUsageFormSet = inlineformset_factory(
    DailyLog, DailyMaterialUsage,
    form=DailyMaterialUsageForm,
    fields=['inventory_item', 'quantity'],
    extra=1,
    can_delete=True
)