from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Bill, BillItem, Item, InventoryLog, Customer, Vendor, Attendance, StudentWorkLog, PurchaseRecord, VendorPayment

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'role', 'emp_id', 'emp_type', 'contact_number')

class UserPermissionsForm(forms.Form):
    user_management = forms.BooleanField(required=False, label="User Management")
    inventory = forms.BooleanField(required=False, label="Inventory & Tracking")
    billing = forms.BooleanField(required=False, label="Billing & Invoices")
    customers = forms.BooleanField(required=False, label="Customer Management")
    vendors = forms.BooleanField(required=False, label="Vendor Management")
    employees = forms.BooleanField(required=False, label="Employee Management")
    attendance = forms.BooleanField(required=False, label="Attendance")
    worklogs = forms.BooleanField(required=False, label="Work Logs")
    purchases = forms.BooleanField(required=False, label="Purchases")
    reports = forms.BooleanField(required=False, label="Reports & Payroll")

    def __init__(self, *args, **kwargs):
        user_permissions = kwargs.pop('initial_permissions', {})
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].initial = user_permissions.get(field, False)

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['customer', 'outlet_name', 'payment_type', 'advance_payment', 'payment_status', 'remarks', 'delivery_date']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'outlet_name': forms.Select(attrs={'class': 'form-select'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'advance_payment': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

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


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['shop_name', 'address', 'contact_number', 'gst_number']
        widgets = {
            'shop_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'
        widgets = {
            'vendor_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'ac_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
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
        fields = ['vendor', 'description', 'total_amount', 'date']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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