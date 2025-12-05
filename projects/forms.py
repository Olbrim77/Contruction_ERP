# projects/forms.py

from django import forms
# FONTOS: modelformset_factory is kell!
from django.forms import inlineformset_factory, modelformset_factory
from .models import (
    Project, Task, Tetelsor, Munkanem, Alvallalkozo, Expense, DailyLog,
    Supplier, Material, MasterItem, ItemComponent, ProjectDocument,
    MaterialOrder, OrderItem, ProjectInventory, DailyMaterialUsage,
    UniclassNode, LaborComponent, MachineComponent, Operation, Machine, DailyLogImage,ProjectChapter, LeaveRequest,
    Employee
)

# --- SEGÉD: Dátum és Uniclass ---
class DateInput(forms.DateInput):
    input_type = 'date'
    format = '%Y-%m-%d'

class UniclassChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if hasattr(obj, 'uniclass_link') and obj.uniclass_link:
            label = obj.uniclass_link.title_hu or obj.uniclass_link.title_en
            return f"[{obj.uniclass_link.code}] {label} --- ({obj.name})"
        return obj.name

# --- NAPI NAPLÓ ŰRLAP ---
class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['date', 'weather', 'workforce', 'work_done', 'problems']
        widgets = {
            'date': DateInput(),
            'work_done': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'problems': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }

# --- NAPLÓ FOTÓ ŰRLAP (Formset-hez) ---
class DailyLogImageForm(forms.ModelForm):
    class Meta:
        model = DailyLogImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'})
        }

# Formset: Ez teszi lehetővé, hogy egyszerre több (pl. 5) képet tölts fel külön mezőkben
DailyLogImageFormSet = inlineformset_factory(
    DailyLog, DailyLogImage,
    form=DailyLogImageForm,
    fields=['image'],
    extra=5,      # 5 üres mezőt jelenít meg alapból
    can_delete=True
)

# --- DOKUMENTUM ŰRLAP ---
class ProjectDocumentForm(forms.ModelForm):
    class Meta:
        model = ProjectDocument
        fields = ['category', 'file', 'description']
        labels = {'category': 'Típus', 'file': 'Fájl', 'description': 'Leírás'}

# EZ HIÁNYZOTT: Formset dokumentumokhoz (pl. 3 db egyszerre)
ProjectDocumentFormSet = modelformset_factory(
    ProjectDocument,
    form=ProjectDocumentForm,
    extra=3,
    can_delete=True
)

# --- RECEPTÚRA ŰRLAPOK ---
class ItemComponentForm(forms.ModelForm):
    material = UniclassChoiceField(queryset=Material.objects.all().order_by('name'), label="Anyag", empty_label="-- Válassz --")
    class Meta: model = ItemComponent; fields = ['material', 'amount']; widgets = {'amount': forms.NumberInput(attrs={'step': '0.01'})}

class LaborComponentForm(forms.ModelForm):
    operation = UniclassChoiceField(queryset=Operation.objects.all().order_by('name'), label="Művelet", empty_label="-- Válassz --")
    class Meta: model = LaborComponent; fields = ['operation', 'time_required']; widgets = {'time_required': forms.NumberInput(attrs={'step': '0.01'})}

class MachineComponentForm(forms.ModelForm):
    machine = UniclassChoiceField(queryset=Machine.objects.all().order_by('name'), label="Gép", empty_label="-- Válassz --")
    class Meta: model = MachineComponent; fields = ['machine', 'amount']; widgets = {'amount': forms.NumberInput(attrs={'step': '0.01'})}

# Formsetek a receptúrához
MaterialInlineFormSet = inlineformset_factory(MasterItem, ItemComponent, form=ItemComponentForm, fields=['material', 'amount'], extra=1, can_delete=True)
LaborInlineFormSet = inlineformset_factory(MasterItem, LaborComponent, form=LaborComponentForm, fields=['operation', 'time_required'], extra=1, can_delete=True)
MachineInlineFormSet = inlineformset_factory(MasterItem, MachineComponent, form=MachineComponentForm, fields=['machine', 'amount'], extra=1, can_delete=True)

# --- EGYÉB ŰRLAPOK (Változatlan) ---
class ProjectForm(forms.ModelForm):
    class Meta: model = Project; fields = '__all__'; widgets = {'inquiry_date': DateInput(), 'callback_date': DateInput(), 'survey_date': DateInput(), 'quote_date': DateInput(), 'contract_date': DateInput(), 'start_date': DateInput(), 'handover_date': DateInput(), 'end_date': DateInput()}
class TaskForm(forms.ModelForm):
    class Meta: model = Task; fields = ['project', 'name', 'due_date']; widgets = {'due_date': DateInput()}
class TetelsorQuantityForm(forms.ModelForm):
    class Meta: model = Tetelsor; fields = ['mennyiseg']; widgets = {'mennyiseg': forms.NumberInput(attrs={'step': '0.01'})}


class TetelsorEditForm(forms.ModelForm):
    material = forms.ModelChoiceField(queryset=Material.objects.all(), required=False, label="Központi Anyag (F)")
    munkanem = forms.ModelChoiceField(queryset=Munkanem.objects.all(), required=False, label="Munkanem (M)")
    alvallalkozo = forms.ModelChoiceField(queryset=Alvallalkozo.objects.all(), required=False, label="Alvállalkozó (O)")

    # ÚJ MEZŐ: Fejezet
    chapter = forms.ModelChoiceField(queryset=ProjectChapter.objects.none(), required=False, label="Fejezet")

    class Meta:
        model = Tetelsor
        # Add hozzá a 'chapter'-t a listához!
        fields = ['chapter', 'mennyiseg', 'leiras', 'egyseg', 'normaido', 'anyag_egysegar', 'material', 'alvallalkozo',
                  'munkanem', 'megjegyzes', 'engy_kod', 'k_jelzo', 'cpr_kod', 'progress_percentage',
                  'labor_split_percentage', 'felelos']
        widgets = {'megjegyzes': forms.Textarea(attrs={'rows': 3}), 'leiras': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Csak az aktuális projekt fejezeteit mutassa
        if self.instance and self.instance.project_id:
            self.fields['chapter'].queryset = ProjectChapter.objects.filter(project=self.instance.project).order_by(
                'rank')
        elif 'initial' in kwargs and 'project' in kwargs['initial']:
            # Ha új tétel létrehozásáról van szó
            self.fields['chapter'].queryset = ProjectChapter.objects.filter(
                project=kwargs['initial']['project']).order_by('rank')
        else:
            # Fallback: minden fejezet (de ez ritkán fordul elő)
            self.fields['chapter'].queryset = ProjectChapter.objects.all()
    class ProjectChapterForm(forms.ModelForm):
        class Meta:
            model = ProjectChapter
            fields = ['name', 'rank']
            labels = {
                'name': 'Fejezet neve (pl. Alapozás, Falszerkezet)',
                'rank': 'Sorrend (pl. 10, 20...)'
            }
            widgets = {
                'rank': forms.NumberInput(attrs={'step': '10', 'class': 'form-control'})
            }



class ExpenseForm(forms.ModelForm):
    class Meta: model = Expense; fields = ['name', 'date', 'category', 'amount_netto', 'invoice_file']; widgets = {'date': DateInput()}
class MaterialOrderForm(forms.ModelForm):
    class Meta: model = MaterialOrder; fields = ['supplier', 'date', 'status', 'notes']; widgets = {'date': DateInput(), 'notes': forms.Textarea(attrs={'rows': 3})}
OrderItemFormSet = inlineformset_factory(MaterialOrder, OrderItem, fields=['name', 'quantity', 'unit', 'price'], extra=1, can_delete=True)
class DailyMaterialUsageForm(forms.ModelForm):
    class Meta: model = DailyMaterialUsage; fields = ['inventory_item', 'quantity']
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None); super().__init__(*args, **kwargs)
        if project: self.fields['inventory_item'].queryset = ProjectInventory.objects.filter(project=project)
DailyMaterialUsageFormSet = inlineformset_factory(DailyLog, DailyMaterialUsage, form=DailyMaterialUsageForm, fields=['inventory_item', 'quantity'], extra=1, can_delete=True)
class TetelsorCreateFromMasterForm(forms.Form):
    master_item = forms.ModelChoiceField(queryset=MasterItem.objects.all()); mennyiseg = forms.DecimalField()
class MasterItemForm(forms.ModelForm):
    class Meta: model = MasterItem; fields = '__all__'; widgets = {'leiras': forms.Textarea(attrs={'rows': 3})}
class MobilePhotoForm(forms.Form):
    image = forms.FileField(label="📷 Fotó készítése", required=False, widget=forms.FileInput(attrs={'capture': 'environment', 'accept': 'image/*', 'class': 'photo-input'}))


class ProjectChapterForm(forms.ModelForm):
    class Meta:
        model = ProjectChapter
        fields = ['name', 'rank']
        labels = {
            'name': 'Fejezet neve (pl. Alapozás)',
            'rank': 'Sorrend (pl. 10, 20...)'
        }
        widgets = {
            'rank': forms.NumberInput(attrs={'step': '10'})

        }


# KÜLÖN, FELSŐ SZINTŰ ŰRLAP: Szabadság igénylés
class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'leave_type', 'reason', 'proof_file']  # proof_file hozzáadva
        widgets = {
            # Mobil naptár megjelenítéséhez
            'start_date': DateInput(),
            'end_date': DateInput(),
            'reason': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Megjegyzés (opcionális)...'}),
            # Fájl feltöltő (képet és pdf-et fogad el)
            'proof_file': forms.FileInput(attrs={'accept': 'image/*,application/pdf', 'class': 'file-input'})
        }


# --- HR: Dolgozó űrlap ---
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'name', 'position', 'phone', 'hourly_wage', 'tax_id', 'address',
            'registration_form', 'contract_file', 'status', 'joined_date', 'user'
        ]
        widgets = {
            'joined_date': DateInput(),
            'hourly_wage': forms.NumberInput(attrs={'step': '1'}),
        }
        labels = {
            'name': 'Név',
            'position': 'Pozíció',
            'phone': 'Telefon',
            'hourly_wage': 'Órabér (Ft)',
            'tax_id': 'Adóazonosító',
            'address': 'Lakcím',
            'registration_form': 'Bejelentő lap',
            'contract_file': 'Munkaszerződés',
            'status': 'Státusz',
            'joined_date': 'Belépés dátuma',
            'user': 'Felhasználói Fiók'
        }