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
    module_permissions = models.JSONField(default=dict, blank=True)

    def is_supervisor_or_admin(self):
        return self.role in ['ADMIN', 'SUPERVISOR']
    
    def has_module_access(self, module_name):
        if self.role == 'ADMIN':
            return True
        # Default permissions based on role if not explicitly set
        if not self.module_permissions:
            if self.role == 'SUPERVISOR':
                return True 
            if self.role == 'ACCOUNTANT' and module_name in ['billing', 'invoices', 'payroll', 'vendor_payments', 'purchases', 'worklogs', 'attendance']:
                return True
            if self.role == 'EMPLOYEE' and module_name in ['billing', 'invoices']:
                 pass
        
        return self.module_permissions.get(module_name, False)

    def save(self, *args, **kwargs):
        # Ensure users with ADMIN or SUPERVISOR roles have admin site access
        if self.role in ['ADMIN', 'SUPERVISOR']:
            self.is_staff = True
        else:
            # do not demote superusers
            if not self.is_superuser:
                self.is_staff = False
        super().save(*args, **kwargs)

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
    bank_name = models.CharField(max_length=200, blank=True)
    ac_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
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
            prefix_map = {'INNER': 'IB', 'OUTER': 'OB', 'SALES': 'SB'}
            prefix = prefix_map.get(self.bill_type, 'INV')
            last_bill = Bill.objects.filter(bill_type=self.bill_type).order_by('id').last()
            # Simple increment logic, might need better concurrency handling in production
            # extracting number from last invoice if possible, else count + 1
            if last_bill and last_bill.invoice_number.startswith(prefix):
                try:
                    last_num = int(last_bill.invoice_number.split('-')[-1])
                    new_id = last_num + 1
                except ValueError:
                    new_id = Bill.objects.count() + 1
            else:
                new_id = 1
            self.invoice_number = f"{prefix}-{new_id:04d}"
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
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    date = models.DateField(default=timezone.now)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    def total_cost(self):
        # Placeholder for cost calculation logic
        return 0 

class PurchaseRecord(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    description = models.TextField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    purchased_by = models.ForeignKey(User, on_delete=models.PROTECT)

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