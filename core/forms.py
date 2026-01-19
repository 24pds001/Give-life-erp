from django import forms
# Force reload
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Bill, BillItem, Item, InventoryLog, Customer, Vendor, Attendance, StudentWorkLog, PurchaseRecord, VendorPayment, BillPayment, InventorySession, InventorySessionItem, InventorySessionPayment

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'role', 'emp_id', 'emp_type', 'contact_number', 'account_holder_name', 'bank_name', 'account_number', 'ifsc_code', 'branch')

class RolePermissionForm(forms.Form):
    # Dynamically generated fields based on RolePermission.get_default_permissions()
    def __init__(self, *args, **kwargs):
        initial_data = kwargs.pop('initial_permissions', {})
        super().__init__(*args, **kwargs)
        
        from .models import RolePermission
        default_perms = RolePermission.get_default_permissions()
        
        # We start with defaults and merge initial data
        # Structure: {module: {action: bool}}
        
        self.modules = list(default_perms.keys())
        self.actions = ['view', 'create', 'edit', 'delete', 'approve'] # Standard actions
        
        for module in self.modules:
            for action in self.actions:
                field_name = f"{module}_{action}"
                initial_val = False
                if module in initial_data and action in initial_data[module]:
                    initial_val = initial_data[module][action]
                elif module in default_perms and action in default_perms[module]:
                     # Fallback to default schema existence check, though values are False usually
                     pass

                self.fields[field_name] = forms.BooleanField(
                    required=False, 
                    initial=initial_val,
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )

    def get_cleaned_permissions(self):
        cleaned_perms = {}
        from .models import RolePermission
        default_perms = RolePermission.get_default_permissions()
        
        for module in default_perms:
            cleaned_perms[module] = {}
            for action in ['view', 'create', 'edit', 'delete', 'approve']:
                field_name = f"{module}_{action}"
                if field_name in self.cleaned_data:
                    cleaned_perms[module][action] = self.cleaned_data[field_name]
        return cleaned_perms

    def get_grid(self):
        # yields (module, [(action, field_bound), ...])
        # This helps templates render a nice grid
        for module in self.modules:
            row = []
            for action in self.actions:
                name = f"{module}_{action}"
                row.append((action, self[name]))
            yield (module.replace('_', ' ').title(), row)

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['customer', 'outlet_name', 'payment_type', 'advance_payment', 'advance_payment_type', 'payment_status', 'remarks', 'delivery_date', 'student_employees']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'outlet_name': forms.Select(attrs={'class': 'form-select'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'advance_payment': forms.NumberInput(attrs={'class': 'form-control'}),
            'advance_payment_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'delivery_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'student_employees': forms.SelectMultiple(attrs={'class': 'form-select', 'id': 'id_student_employees'}),
        }

class BillPaymentForm(forms.ModelForm):
    class Meta:
        model = BillPayment
        fields = ['payment_type', 'amount', 'reference_number']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Amount'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ref No. (Optional)'}),
        }

BillPaymentFormSet = inlineformset_factory(
    Bill, BillPayment, form=BillPaymentForm,
    extra=0, can_delete=True
)

class BillItemForm(forms.ModelForm):
    class Meta:
        model = BillItem
        fields = ['item', 'custom_item_name', 'quantity', 'price']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select item-selector'}),
            'custom_item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-control price-input'}),
        }

BillItemFormSet = inlineformset_factory(
    Bill, BillItem, form=BillItemForm, extra=1, can_delete=True
)

class InventoryLogForm(forms.ModelForm):
    class Meta:
        model = InventoryLog
        fields = ['outlet_name', 'item', 'quantity_taken']
        widgets = {
            'outlet_name': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity_taken': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class InventorySessionForm(forms.ModelForm):
    class Meta:
        model = InventorySession
        fields = ['outlet_name', 'student_employees', 'payment_status']
        widgets = {
            'outlet_name': forms.Select(attrs={'class': 'form-select'}),
            'student_employees': forms.SelectMultiple(attrs={'class': 'form-select', 'id': 'id_student_employees'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }

class InventorySessionPaymentForm(forms.ModelForm):
    class Meta:
        model = InventorySessionPayment
        fields = ['payment_type', 'amount', 'reference_number']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Amount'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ref No.'}),
        }

InventorySessionPaymentFormSet = inlineformset_factory(
    InventorySession, InventorySessionPayment, form=InventorySessionPaymentForm,
    extra=0, can_delete=True
)

class InventorySessionItemForm(forms.ModelForm):
    class Meta:
        model = InventorySessionItem
        fields = ['item', 'quantity_taken', 'quantity_returned']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select product-select'}),
            'quantity_taken': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity_returned': forms.NumberInput(attrs={'class': 'form-control'}),
        }

InventorySessionItemFormSet = inlineformset_factory(
    InventorySession, InventorySessionItem, form=InventorySessionItemForm,
    extra=1, can_delete=True
)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_name', 'address', 'contact_number', 'email_id']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email_id': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'
        widgets = {
            'vendor_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_holder_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'ac_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['date', 'in_time', 'out_time']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

class StudentWorkLogForm(forms.ModelForm):
    class Meta:
        model = StudentWorkLog
        fields = ['date', 'working_hours', 'overtime_hours']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'working_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PurchaseRecordForm(forms.ModelForm):
    class Meta:
        model = PurchaseRecord
        fields = ['vendor', 'bill_no', 'description', 'total_amount', 'ordered_date', 'received_date', 'payment_type', 'payment_status', 'payment_date']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'bill_no': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'ordered_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'received_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class VendorPaymentForm(forms.ModelForm):
    class Meta:
        model = VendorPayment
        fields = ['vendor', 'amount', 'date', 'status', 'details']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }