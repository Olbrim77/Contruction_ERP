# projects/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog,
    Supplier, Material, MasterItem, ItemComponent, ProjectDocument,
    MaterialOrder, OrderItem, ProjectInventory, DailyMaterialUsage,
    UniclassNode, LaborComponent, MachineComponent, Operation, Machine
)

# --- DÁTUM MEZŐ ---
class DateInput(forms.DateInput):
    input_type = 'date'
    format = '%Y-%m-%d'

# --- UNICLASS OKOS VÁLASZTÓ ---
class UniclassChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Ha van Uniclass kapcsolat, kiírjuk a kódot és a nevet is
        if hasattr(obj, 'uniclass_link') and obj.uniclass_link:
            label = obj.uniclass_link.title_hu or obj.uniclass_link.title_en
            return f"[{obj.uniclass_link.code}] {label} --- ({obj.name})"
        return obj.name

# --- RECEPTÚRA SOROK (KOMPONENSEK) ---

class ItemComponentForm(forms.ModelForm):
    material = UniclassChoiceField(
        queryset=Material.objects.all().order_by('name'),
        label="Anyag",
        empty_label="-- Válassz Anyagot --"
    )
    class Meta:
        model = ItemComponent
        fields = ['material', 'amount']
        widgets = {'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': 'Mennyiség'})}

class LaborComponentForm(forms.ModelForm):
    operation = UniclassChoiceField(
        queryset=Operation.objects.all().order_by('name'),
        label="Művelet",
        empty_label="-- Válassz Műveletet --"
    )
    class Meta:
        model = LaborComponent
        fields = ['operation', 'time_required']
        labels = {'time_required': 'Norma (óra)'}
        widgets = {'time_required': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': 'Óra'})}

class MachineComponentForm(forms.ModelForm):
    machine = UniclassChoiceField(
        queryset=Machine.objects.all().order_by('name'),
        label="Gép",
        empty_label="-- Válassz Gépet --"
    )
    class Meta:
        model = MachineComponent
        fields = ['machine', 'amount']
        labels = {'amount': 'Használat (óra)'}
        widgets = {'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': 'Óra'})}

# --- FORMSETEK (A TÁBLÁZATOKHOZ) ---
MaterialInlineFormSet = inlineformset_factory(
    MasterItem, ItemComponent, form=ItemComponentForm,
    fields=['material', 'amount'], extra=1, can_delete=True
)

LaborInlineFormSet = inlineformset_factory(
    MasterItem, LaborComponent, form=LaborComponentForm,
    fields=['operation', 'time_required'], extra=1, can_delete=True
)

MachineInlineFormSet = inlineformset_factory(
    MasterItem, MachineComponent, form=MachineComponentForm,
    fields=['machine', 'amount'], extra=1, can_delete=True
)

# --- EGYÉB ŰRLAPOK ---
class MasterItemForm(forms.ModelForm):
    class Meta:
        model = MasterItem
        fields = '__all__'
        widgets = {'leiras': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})}

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'inquiry_date': DateInput(), 'callback_date': DateInput(), 'survey_date': DateInput(),
            'quote_date': DateInput(), 'contract_date': DateInput(), 'start_date': DateInput(),
            'handover_date': DateInput(), 'end_date': DateInput()
        }

class TaskForm(forms.ModelForm):
    class Meta: model = Task; fields = ['project', 'name', 'due_date']; widgets = {'due_date': DateInput()}

class TetelsorQuantityForm(forms.ModelForm):
    class Meta: model = Tetelsor; fields = ['mennyiseg']; widgets = {'mennyiseg': forms.NumberInput(attrs={'step': '0.01'})}

class TetelsorEditForm(forms.ModelForm):
    material = forms.ModelChoiceField(queryset=Material.objects.all(), required=False)
    munkanem = forms.ModelChoiceField(queryset=Munkanem.objects.all(), required=False)
    alvallalkozo = forms.ModelChoiceField(queryset=Alvallalkozo.objects.all(), required=False)
    class Meta:
        model = Tetelsor
        fields = ['mennyiseg', 'leiras', 'egyseg', 'normaido', 'anyag_egysegar', 'material', 'alvallalkozo', 'munkanem', 'megjegyzes', 'engy_kod', 'k_jelzo', 'cpr_kod', 'progress_percentage', 'labor_split_percentage', 'felelos']
        widgets = {'megjegyzes': forms.Textarea(attrs={'rows': 3}), 'leiras': forms.Textarea(attrs={'rows': 3})}

class ExpenseForm(forms.ModelForm):
    class Meta: model = Expense; fields = ['name', 'date', 'category', 'amount_netto', 'invoice_file']; widgets = {'date': DateInput()}

class DailyLogForm(forms.ModelForm):
    class Meta: model = DailyLog; fields = ['date', 'weather', 'workforce', 'work_done', 'problems']; widgets = {'date': DateInput(), 'work_done': forms.Textarea(attrs={'rows': 5}), 'problems': forms.Textarea(attrs={'rows': 3})}

class ProjectDocumentForm(forms.ModelForm):
    class Meta: model = ProjectDocument; fields = ['category', 'file', 'description']

class MaterialOrderForm(forms.ModelForm):
    class Meta: model = MaterialOrder; fields = ['supplier', 'date', 'status', 'notes']; widgets = {'date': DateInput(), 'notes': forms.Textarea(attrs={'rows': 3})}

OrderItemFormSet = inlineformset_factory(MaterialOrder, OrderItem, fields=['name', 'quantity', 'unit', 'price'], extra=1, can_delete=True)

class DailyMaterialUsageForm(forms.ModelForm):
    class Meta: model = DailyMaterialUsage; fields = ['inventory_item', 'quantity']
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project: self.fields['inventory_item'].queryset = ProjectInventory.objects.filter(project=project)

DailyMaterialUsageFormSet = inlineformset_factory(DailyLog, DailyMaterialUsage, form=DailyMaterialUsageForm, fields=['inventory_item', 'quantity'], extra=1, can_delete=True)

class TetelsorCreateFromMasterForm(forms.Form):
    master_item = forms.ModelChoiceField(queryset=MasterItem.objects.all())
    mennyiseg = forms.DecimalField()

class MobilePhotoForm(forms.Form):
    image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'capture': 'environment'}))