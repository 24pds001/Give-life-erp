from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('ACCOUNTANT', 'Accountant'),
        ('SUPERVISOR', 'Supervisor'),
        ('EMPLOYEE', 'Regular Employee'),
        ('STUDENT', 'Student Employee'),
    )
    EMP_TYPE_CHOICES = (
        ('PARTTIME', 'Part-Time'),
        ('REGULAR', 'Regular'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    emp_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    emp_type = models.CharField(max_length=20, choices=EMP_TYPE_CHOICES, null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    
    # Bank Details
    account_holder_name = models.CharField(max_length=200, blank=True)
    bank_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    branch = models.CharField(max_length=100, blank=True)

    module_permissions = models.JSONField(default=dict, blank=True)

    def is_supervisor_or_admin(self):
        return self.role in ['ADMIN', 'SUPERVISOR']
    
    def has_module_access(self, module_name, action=None):
        if self.role == 'ADMIN':
            return True
            
        # 1. Check User-specific override
        if self.module_permissions and module_name in self.module_permissions:
            user_perm = self.module_permissions[module_name]
            if isinstance(user_perm, bool): # Backward compatibility or simple switch
                 return user_perm
            if action and isinstance(user_perm, dict):
                return user_perm.get(action, False)
            return True # Fallback if just present? Or should strict check? 
            # If we move to granular, we expect dict. 
            # If it's a legacy simple 'billing': True, then it implies full access or at least 'view'.
            # Let's assume True means full access for now to be safe, or just return True.

        # 2. Check Role-based permissions
        try:
            role_perm = RolePermission.objects.get(role=self.role)
            perms = role_perm.permissions.get(module_name, {})
            if action:
                return perms.get(action, False)
            # If no action specified, check if they have 'view' or any access
            return perms.get('view', False) or any(perms.values())
        except RolePermission.DoesNotExist:
            # Fallback to hardcoded defaults for safety during migration
             return self._get_legacy_permission(module_name)

    def _get_legacy_permission(self, module_name):
        # Default permissions based on role if not explicitly set
        if self.role == 'SUPERVISOR':
            return True 
        if self.role == 'ACCOUNTANT' and module_name in ['billing', 'invoices', 'payroll', 'vendor_payments', 'purchases', 'worklogs', 'attendance']:
            return True
        if self.role == 'EMPLOYEE' and module_name in ['billing', 'invoices']:
             pass # Logic was pass? implies False default return at end.
             return True
        if self.role == 'STUDENT' and module_name == 'inventory':
            return True
        return False

    def save(self, *args, **kwargs):
        # Ensure users with ADMIN or SUPERVISOR roles have admin site access
        if self.role in ['ADMIN', 'SUPERVISOR']:
            self.is_staff = True
        else:
            # do not demote superusers
            if not self.is_superuser:
                self.is_staff = False
        super().save(*args, **kwargs)

class RolePermission(models.Model):
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, unique=True)
    permissions = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_role_display()

    @staticmethod
    def get_default_permissions():
        # Schema: { 'module': { 'action': boolean } }
        # Actions: view, create, edit, delete, approve
        modules = ['users', 'items', 'customers', 'sales_bill', 'outer_bill', 'inner_bill', 'inventory', 'vendors', 'employees', 'attendance', 'worklogs', 'purchases', 'vendor_payments', 'payroll', 'reports']
        return {m: {'view': False, 'create': False, 'edit': False, 'delete': False, 'approve': False} for m in modules}

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255) # e.g., "Login", "Logout", "Created Bill #123"
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"

class Item(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Customer(models.Model):
    customer_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    email_id = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.customer_name

class Vendor(models.Model):
    vendor_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    account_holder_name = models.CharField(max_length=200, blank=True)
    bank_name = models.CharField(max_length=200, blank=True)
    ac_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    contact = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Bill(models.Model):
    BILL_TYPES = (
        ('INNER', 'Inner Bill'),
        ('OUTER', 'Outer Bill'),
        ('SALES', 'Sales Bill'),
    )
    PAYMENT_STATUS = (
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
    )
    PAYMENT_TYPE_CHOICES = (
        ('UPI', 'UPI'),
        ('CASH', 'Cash'),
        ('ONLINE', 'Online'),
        ('CHEQUE', 'Cheque'),
        ('CARD', 'Card'),
        ('NEFT', 'NEFT/IMPS'),
    )
    OUTLET_CHOICES = (
        ('EAT_RIGHT', 'Eat Right'),
        ('BED', 'B.Ed'),
        ('LIBA', 'Liba'),
        ('MOBILE_1', 'Mobile Shop 1'),
        ('MOBILE_2', 'Mobile Shop 2'),
        ('MOBILE_3', 'Mobile Shop 3'),
    )

    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    bill_type = models.CharField(max_length=10, choices=BILL_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    # For Outer bills where customer might not be in DB, or just name/address is needed
    customer_name = models.CharField(max_length=200, blank=True)
    customer_address = models.TextField(blank=True)
    
    outlet_name = models.CharField(max_length=50, choices=OUTLET_CHOICES, null=True, blank=True)
    
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='CASH') 
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    advance_payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, null=True, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')
    remarks = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_date = models.DateField(null=True, blank=True)
    
    student_employees = models.ManyToManyField(User, related_name='assisted_bills', blank=True, limit_choices_to={'role': 'STUDENT'})

    @property
    def balance_due(self):
        return self.total_amount - self.advance_payment



    def save(self, *args, **kwargs):
        if not self.invoice_number:
            today_str = timezone.now().strftime('%Y%m%d')
            prefix_map = {'INNER': 'IB', 'OUTER': 'OB', 'SALES': 'SB'}
            prefix = prefix_map.get(self.bill_type, 'INV')
            base_id = f"{prefix}-{today_str}"
            
            # Find last bill with this prefix and date
            last_bill = Bill.objects.filter(invoice_number__startswith=base_id).order_by('invoice_number').last()
            
            if last_bill:
                try:
                    # Extract sequence number (last 4 digits)
                    last_seq = int(last_bill.invoice_number[-4:])
                    new_seq = last_seq + 1
                except ValueError:
                    new_seq = 1
            else:
                new_seq = 1
            
            self.invoice_number = f"{base_id}{new_seq:04d}"
        super().save(*args, **kwargs)

class BillPayment(models.Model):
    bill = models.ForeignKey(Bill, related_name='payments', on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=20, choices=Bill.PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    custom_item_name = models.CharField(max_length=200, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total(self):
        return self.quantity * self.price

class InventoryLog(models.Model):
    outlet_name = models.CharField(max_length=50, choices=Bill.OUTLET_CHOICES)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity_taken = models.PositiveIntegerField(default=0)
    quantity_returned = models.PositiveIntegerField(default=0, null=True, blank=True)
    date_issued = models.DateTimeField(auto_now_add=True)
    date_returned = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

class InventorySession(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    )
    outlet_name = models.CharField(max_length=50, choices=Bill.OUTLET_CHOICES)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=200, blank=True)
    student_employees = models.ManyToManyField(User, related_name='assisted_inventory_sessions', blank=True, limit_choices_to={'role': 'STUDENT'})
    payment_status = models.CharField(max_length=10, choices=Bill.PAYMENT_STATUS, default='PENDING')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    
    def __str__(self):
        return f"{self.get_outlet_name_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class InventorySessionItem(models.Model):
    session = models.ForeignKey(InventorySession, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity_taken = models.PositiveIntegerField(default=0)
    quantity_returned = models.PositiveIntegerField(default=0)
    
    @property
    def quantity_sold(self):
        return max(0, self.quantity_taken - self.quantity_returned)

class InventorySessionPayment(models.Model):
    session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=Bill.PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.payment_type} - {self.amount}"

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    in_time = models.TimeField()
    out_time = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_approved = models.BooleanField(default=False) # Approved by accountant

class StudentWorkLog(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    date = models.DateField(default=timezone.now)
    entry_time = models.TimeField(null=True, blank=True)
    exit_time = models.TimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    def total_cost(self):
        # Placeholder for cost calculation logic
        return 0 


class PurchaseRecord(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    purchase_order_id = models.CharField(max_length=50, unique=True, blank=True)
    bill_no = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    ordered_date = models.DateField(default=timezone.now)
    received_date = models.DateField(null=True, blank=True)
    payment_type = models.CharField(max_length=20, choices=Bill.PAYMENT_TYPE_CHOICES, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=Bill.PAYMENT_STATUS, default='PENDING')
    payment_date = models.DateField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    purchased_by = models.ForeignKey(User, on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        if not self.purchase_order_id:
            today_str = timezone.now().strftime('%Y%m%d')
            prefix = "PO"
            base_id = f"{prefix}-{today_str}"
            
            # Find last PO with this prefix and date
            last_po = PurchaseRecord.objects.filter(purchase_order_id__startswith=base_id).order_by('purchase_order_id').last()
            
            if last_po:
                try:
                    # Extract sequence number (last 4 digits)
                    last_seq = int(last_po.purchase_order_id[-4:])
                    new_seq = last_seq + 1
                except ValueError:
                    new_seq = 1
            else:
                new_seq = 1
            
            self.purchase_order_id = f"{base_id}{new_seq:04d}"
        super().save(*args, **kwargs)

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(PurchaseRecord, related_name='items', on_delete=models.CASCADE)
    item_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total(self):
        return self.quantity * self.price

class VendorPayment(models.Model):
    PAYMENT_STATUS = (
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
    )
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    approval_status = models.BooleanField(default=False) # Approved by supervisor/accountant
    details = models.TextField(blank=True)