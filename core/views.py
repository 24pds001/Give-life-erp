from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from .models import User, Item, Bill, BillItem, InventoryLog, Customer, Vendor, Attendance, StudentWorkLog, PurchaseRecord, VendorPayment, RolePermission
from .forms import CustomUserCreationForm, BillForm, BillItemFormSet, ItemForm, InventoryLogForm, CustomerForm, VendorForm, AttendanceForm, StudentWorkLogForm, PurchaseRecordForm, VendorPaymentForm, RolePermissionForm, BillPaymentFormSet
import json
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.template.loader import render_to_string
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False

def is_admin(user):
    return user.role == 'ADMIN'

def check_permission(user, module):
    return user.is_authenticated and user.has_module_access(module)

@login_required
def dashboard(request):
    today = timezone.now().date()
    daily_sales = Bill.objects.filter(created_at__date=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    pending_payments = Bill.objects.filter(payment_status='PENDING').count()
    recent_bills = Bill.objects.all().order_by('-created_at')[:10]
    query = request.GET.get('q')
    if query:
        recent_bills = Bill.objects.filter(invoice_number__icontains=query)
    # Module counts
    if request.user.has_module_access('billing'):
        invoices_count = Bill.objects.count() if request.user.is_supervisor_or_admin() else Bill.objects.filter(created_by=request.user).count()
    else:
        invoices_count = 0
        
    items_count = Item.objects.count() if request.user.has_module_access('inventory') else 0
    vendors_count = Customer.objects.count() if request.user.has_module_access('customers') else 0
    inventory_count = InventoryLog.objects.count() if request.user.has_module_access('inventory') else 0

    context = {
        'daily_sales': daily_sales,
        'pending_payments': pending_payments,
        'recent_bills': recent_bills,
        'invoices_count': invoices_count,
        'items_count': items_count,
        'vendors_count': vendors_count,
        'inventory_count': inventory_count,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
@user_passes_test(lambda u: check_permission(u, 'user_management'))
def user_list(request):
    users = User.objects.all()
    return render(request, 'core/user_list.html', {'users': users})

@login_required
@user_passes_test(lambda u: check_permission(u, 'user_management'))
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully")
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Create User'})

from .models import User, Bill, BillItem, Item, InventoryLog, Customer, Vendor, BillPayment, Attendance, StudentWorkLog, PurchaseRecord, PurchaseItem, VendorPayment, ActivityLog, RolePermission
from .forms import (
    CustomUserCreationForm, BillForm, BillItemFormSet, InventoryLogForm, ItemForm, 
    CustomerForm, VendorForm, BillPaymentFormSet, AttendanceForm, StudentWorkLogForm,
    PurchaseRecordForm, VendorPaymentForm, RolePermissionForm
)
# ... checks ...

@login_required
@user_passes_test(lambda u: u.role == 'ADMIN')
def manage_user_permissions(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = RolePermissionForm(request.POST, initial_permissions={}) # Initial not strictly needed for POST but good practice?
        if form.is_valid():
            user_to_edit.module_permissions = form.get_cleaned_permissions()
            user_to_edit.save()
            messages.success(request, f"Permissions updated for {user_to_edit.username}")
            return redirect('user_list')
    else:
        form = RolePermissionForm(initial_permissions=user_to_edit.module_permissions)
    
    return render(request, 'core/user_permissions.html', {'form': form, 'user_to_edit': user_to_edit, 'title': 'Manage User Permissions'})

@login_required
@user_passes_test(lambda u: u.role == 'ADMIN')
def role_list(request):
    roles = []
    for code, name in User.ROLE_CHOICES:
        perm_count = 0
        try:
             rp = RolePermission.objects.get(role=code)
             # rough count of enabled actions
             for mod in rp.permissions:
                 perm_count += sum(1 for v in rp.permissions[mod].values() if v)
        except RolePermission.DoesNotExist:
             pass
        roles.append({'code': code, 'name': name, 'perm_count': perm_count})
        
    return render(request, 'core/role_list.html', {'roles': roles})

@login_required
@user_passes_test(lambda u: u.role == 'ADMIN')
def edit_role_permissions(request, role_code):
    # Ensure role_code is valid
    valid_roles = [c for c, n in User.ROLE_CHOICES]
    if role_code not in valid_roles:
        messages.error(request, "Invalid Role")
        return redirect('role_list')
        
    role_perm, created = RolePermission.objects.get_or_create(role=role_code)
    
    if request.method == 'POST':
        form = RolePermissionForm(request.POST)
        if form.is_valid():
            role_perm.permissions = form.get_cleaned_permissions()
            role_perm.save()
            messages.success(request, f"Permissions updated for role {role_perm.get_role_display()}")
            return redirect('role_list')
    else:
        form = RolePermissionForm(initial_permissions=role_perm.permissions)
        
    return render(request, 'core/role_permissions_form.html', {
        'form': form, 
        'role_name': role_perm.get_role_display(),
        'role_code': role_code
    })

@login_required
def profile(request):
    if request.method == 'POST':
        # allow password change here
        pwd_form = PasswordChangeForm(request.user, request.POST)
        if pwd_form.is_valid():
            user = pwd_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully')
            return redirect('profile')
    else:
        pwd_form = PasswordChangeForm(request.user)
    return render(request, 'core/profile.html', {'pwd_form': pwd_form})

@login_required
@user_passes_test(lambda u: check_permission(u, 'inventory'))
def inventory_list(request):
    logs = InventoryLog.objects.all().order_by('-date_issued')
    return render(request, 'core/inventory_list.html', {'logs': logs})

@login_required
@user_passes_test(lambda u: check_permission(u, 'inventory'))
def create_inventory_log(request):
    if request.method == 'POST':
        form = InventoryLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.created_by = request.user
            log.save()
            return redirect('inventory_list')
    else:
        form = InventoryLogForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Log Inventory Out'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'inventory'))
def close_inventory_log(request, pk):
    log = get_object_or_404(InventoryLog, pk=pk)
    if log.is_closed:
        return redirect('inventory_list')
    if request.method == 'POST':
        qty_returned = int(request.POST.get('quantity_returned', 0))
        log.quantity_returned = qty_returned
        log.date_returned = timezone.now()
        log.is_closed = True
        log.save()
        sold_qty = log.quantity_taken - log.quantity_returned
        if sold_qty > 0:
            new_bill = Bill.objects.create(
                bill_type='SALES', created_by=request.user,
                outlet_name=log.outlet_name, payment_type='CASH',
                payment_status='PENDING', remarks=f"Auto-generated from Inventory Log #{log.id}"
            )
            BillItem.objects.create(
                bill=new_bill, item=log.item, quantity=sold_qty, price=log.item.price
            )
            new_bill.total_amount = sold_qty * log.item.price
            new_bill.save()
            messages.success(request, f"Inventory Closed. Sales Bill {new_bill.invoice_number} Created.")
            return redirect('bill_detail', pk=new_bill.id)
        return redirect('inventory_list')
    return render(request, 'core/inventory_close.html', {'log': log})

@login_required
@user_passes_test(lambda u: check_permission(u, 'inventory'))
def item_list(request):
    items = Item.objects.all()
    return render(request, 'core/item_list.html', {'items': items})

@login_required
@user_passes_test(lambda u: check_permission(u, 'customers'))
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'core/customer_list.html', {'customers': customers})

@login_required
@user_passes_test(lambda u: check_permission(u, 'customers'))
def create_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Add Customer'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'customers'))
def edit_customer(request, pk):
    cust = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=cust)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=cust)
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Edit Customer'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'customers'))
def delete_customer(request, pk):
    cust = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        cust.delete()
        return redirect('customer_list')
    return render(request, 'core/form_generic.html', {'form': None, 'title': f'Delete Customer {cust.customer_name}', 'object': cust})

@login_required
@user_passes_test(lambda u: check_permission(u, 'inventory'))
def create_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('item_list')
    else:
        form = ItemForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Add Item'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'inventory'))
def edit_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('item_list')
    else:
        form = ItemForm(instance=item)
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Edit Item'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'inventory'))
def delete_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    item.delete()
    return redirect('item_list')

@login_required
@user_passes_test(lambda u: check_permission(u, 'billing'))
def billing_home(request):
    # Fetch bills based on permissions
    if request.user.is_supervisor_or_admin() or request.user.has_module_access('billing'):
        qs = Bill.objects.all().order_by('-created_at')
    else:
        qs = Bill.objects.filter(created_by=request.user).order_by('-created_at')

    # Filters
    bill_type = request.GET.get('bill_type')
    payment_status = request.GET.get('payment_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    q = request.GET.get('q')

    if bill_type:
        qs = qs.filter(bill_type=bill_type)
    if payment_status:
        qs = qs.filter(payment_status=payment_status)
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            qs = qs.filter(created_at__gte=sd)
        except Exception:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            qs = qs.filter(created_at__lte=ed)
        except Exception:
            pass
    if q:
        qs = qs.filter(Q(invoice_number__icontains=q) | Q(customer__customer_name__icontains=q) | Q(customer_name__icontains=q))

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 20) # Show 20 per page
    try:
        bills = paginator.page(page)
    except PageNotAnInteger:
        bills = paginator.page(1)
    except EmptyPage:
        bills = paginator.page(paginator.num_pages)

    context = {
        'bills': bills,
        'filter_bill_type': bill_type,
        'filter_payment_status': payment_status,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'q': q,
    }
    return render(request, 'core/billing_home.html', context)

@login_required
@user_passes_test(lambda u: check_permission(u, 'billing'))
def create_bill(request, bill_type):
    if bill_type == 'INNER':
        template_name = 'core/bill_form_inner.html'
    elif bill_type == 'OUTER':
        template_name = 'core/bill_form_outer.html'
    else:
        template_name = 'core/bill_form_sales.html'

    items = Item.objects.all()
    if request.method == 'POST':
        form = BillForm(request.POST)

        formset = BillItemFormSet(request.POST)
        
        valid = form.is_valid() and formset.is_valid()
        
        payment_formset = None
        if bill_type == 'SALES':
            payment_formset = BillPaymentFormSet(request.POST, prefix='payments')
            valid = valid and payment_formset.is_valid()
        
        # Specific validation for Inner and Outer Bills
        
        # Specific validation for Inner and Outer Bills
        if bill_type in ['INNER', 'OUTER']:
            type_label = "Inner" if bill_type == 'INNER' else "Outer"
            if not form.cleaned_data.get('customer'):
                form.add_error('customer', f"Customer is required for {type_label} Bills.")
                valid = False
            if not form.cleaned_data.get('delivery_date'):
                form.add_error('delivery_date', f"Delivery Date is required for {type_label} Bills.")
                valid = False
                
        # Specific validation for Sales Bill (Mobile Shop)
        if bill_type == 'SALES':
            outlet = form.cleaned_data.get('outlet_name')
            if not outlet:
                 form.add_error('outlet_name', "Outlet is required for Sales bills.")
                 valid = False
            elif outlet in ['MOBILE_1', 'MOBILE_2', 'MOBILE_3']:
                if not form.cleaned_data.get('student_employees'):
                    form.add_error('student_employees', "Please select at least one student employee.")
                    valid = False
                
        if valid:
            # 1. Aggregate items first to check if we have any valid items
            aggregated = {}
            for subform in formset:
                if not subform.cleaned_data or subform.cleaned_data.get('DELETE', False):
                    continue
                cd = subform.cleaned_data
                item = cd.get('item')
                custom_name = cd.get('custom_item_name') or ''
                qty = int(cd.get('quantity') or 0)
                price = cd.get('price')
                
                if qty <= 0:
                    continue

                if item and (price is None or price == ''):
                    price = item.price
                # normalize price to Decimal
                price = Decimal(price or 0)
                key = (f'item:{item.id}' if item else f'custom:{custom_name.strip()}', str(price))
                if key in aggregated:
                    aggregated[key]['quantity'] += qty
                else:
                    aggregated[key] = {'item': item, 'custom_item_name': custom_name, 'price': price, 'quantity': qty}
            
            # 2. Check if empty
            if not aggregated:
                # messages.error(request, "Cannot generate a bill with no items. Please add at least one item.")
                form.add_error(None, "Cannot generate a bill with no items. Please add at least one item.")
                
                items = Item.objects.all()
                items_mapping = {item.id: str(item.price) for item in items}
                if bill_type == 'INNER':
                    template_name = 'core/bill_form_inner.html'
                elif bill_type == 'OUTER':
                    template_name = 'core/bill_form_outer.html'
                else:
                    template_name = 'core/bill_form_sales.html'

                return render(request, template_name, {
                    'form': form,
                    'formset': formset,
                    'payment_formset': payment_formset, # ensure this is passed
                    'bill_type': bill_type,
                    'items': items,
                    'items_json': json.dumps(items_mapping)
                })

            # 2.5 Validation: Total Paid must match Grand Total for SALES bills (Only if PAID)
            if bill_type == 'SALES':
                # Check status
                payment_status = form.cleaned_data.get('payment_status')
                
                if payment_status == 'PAID':
                    # Calculate Grand Total
                    grand_total = Decimal('0')
                    for v in aggregated.values():
                        grand_total += v['price'] * v['quantity']
                    
                    # Calculate Total Paid
                    total_paid = Decimal('0')
                    if payment_formset:
                        for p_form in payment_formset:
                            if p_form.cleaned_data and not p_form.cleaned_data.get('DELETE'):
                                 amount = p_form.cleaned_data.get('amount') or Decimal('0')
                                 if amount <= 0:
                                     p_form.add_error('amount', "Payment amount must be greater than 0.")
                                     items = Item.objects.all()
                                     items_mapping = {item.id: str(item.price) for item in items}
                                     return render(request, template_name, {
                                        'form': form,
                                        'formset': formset,
                                        'payment_formset': payment_formset,
                                        'bill_type': bill_type,
                                        'items': items,
                                        'items_json': json.dumps(items_mapping)
                                     })
                                 total_paid += amount
                    
                    if abs(total_paid - grand_total) > Decimal('0.5'):
                        form.add_error(None, f"Total Paid ({total_paid}) must match Grand Total ({grand_total}) for Paid Sales Bills.")
                        
                        items = Item.objects.all()
                        items_mapping = {item.id: str(item.price) for item in items}
                        return render(request, template_name, {
                            'form': form,
                            'formset': formset,
                            'payment_formset': payment_formset,
                            'bill_type': bill_type,
                            'items': items,
                            'items_json': json.dumps(items_mapping)
                        })

                        return render(request, template_name, {
                            'form': form,
                            'formset': formset,
                            'payment_formset': payment_formset,
                            'bill_type': bill_type,
                            'items': items,
                            'items_json': json.dumps(items_mapping)
                        })

            # 2.6 Validation: Advance Payment for OUTER bills
            if bill_type == 'OUTER':
                payment_status = form.cleaned_data.get('payment_status')
                advance_payment = form.cleaned_data.get('advance_payment') or Decimal('0')
                
                # Calculate Grand Total (Reuse logic or recalculate)
                grand_total = Decimal('0')
                for v in aggregated.values():
                    grand_total += v['price'] * v['quantity']
                
                if payment_status == 'PENDING':
                    if advance_payment < 0:
                         form.add_error('advance_payment', "Advance payment cannot be negative.")
                         items = Item.objects.all()
                         items_mapping = {item.id: str(item.price) for item in items}
                         return render(request, template_name, {
                            'form': form,
                            'formset': formset,
                            'payment_formset': payment_formset,
                            'bill_type': bill_type,
                            'items': items,
                            'items_json': json.dumps(items_mapping)
                        })
                    elif advance_payment >= grand_total:
                         form.add_error('advance_payment', "Advance payment must be less than Total Amount for pending bills. Please mark as PAID or reduce advance amount.")
                         items = Item.objects.all()
                         items_mapping = {item.id: str(item.price) for item in items}
                         return render(request, template_name, {
                            'form': form,
                            'formset': formset,
                            'payment_formset': payment_formset,
                            'bill_type': bill_type,
                            'items': items,
                            'items_json': json.dumps(items_mapping)
                        })

            # 3. Save Bill and Items
            bill = form.save(commit=False)
            bill.bill_type = bill_type
            bill.created_by = request.user
            bill.save()
            form.save_m2m() # Save student_employees relation
            
            total = Decimal('0')
            for v in aggregated.values():
                bi = BillItem.objects.create(
                    bill=bill,
                    item=v['item'],
                    custom_item_name=v['custom_item_name'] or None,
                    quantity=v['quantity'],
                    price=v['price']
                )
                total += Decimal(bi.price) * bi.quantity
            bill.total_amount = total
            bill.save()
            
            # Save payments (only for SALES)
            if payment_formset:
                payments = payment_formset.save(commit=False)
                for payment in payments:
                    payment.bill = bill
                    payment.save()
                for obj in payment_formset.deleted_objects:
                    obj.delete()

            messages.success(request, "Bill Generated Successfully")
            return redirect('bill_detail', pk=bill.id)
    else:
        form = BillForm()
        formset = BillItemFormSet()
        payment_formset = BillPaymentFormSet(prefix='payments')
    items = Item.objects.all()
    items_mapping = {item.id: str(item.price) for item in items}
    return render(request, template_name, {
        'form': form,
        'formset': formset,
        'payment_formset': payment_formset,
        'bill_type': bill_type,
        'items': items,
        'items_json': json.dumps(items_mapping)
    })

@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    
    # Check permission
    can_view = False
    if request.user.role in ['ADMIN', 'SUPERVISOR', 'ACCOUNTANT']:
        can_view = True
    elif bill.created_by == request.user:
        can_view = True
    elif request.user.has_module_access('billing'):
        can_view = True
    # Detailed check based on bill type
    elif request.user.has_module_access('sales_bill') and bill.bill_type == 'SALES':
        can_view = True
    elif request.user.has_module_access('outer_bill') and bill.bill_type == 'OUTER':
        can_view = True
    elif request.user.has_module_access('inner_bill') and bill.bill_type == 'INNER':
        can_view = True
        
    if not can_view:
         messages.error(request, "Unauthorized to view this bill")
         return redirect('dashboard')
         
    return render(request, 'core/bill_print.html', {'bill': bill})

@login_required
@user_passes_test(lambda u: check_permission(u, 'billing'))
def bill_list(request):
    # If admin/supervisor, see all.
    # If employee with billing access, see all? or just their own?
    # Usually billing staff needs to see all bills to manage them.
    if request.user.is_supervisor_or_admin() or request.user.has_module_access('billing'):
        qs = Bill.objects.all().order_by('-created_at')
    else:
        qs = Bill.objects.filter(created_by=request.user).order_by('-created_at')

    # Filters
    bill_type = request.GET.get('bill_type')
    payment_status = request.GET.get('payment_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    sort_by = request.GET.get('sort_by', 'date_desc')
    q = request.GET.get('q')

    if bill_type:
        qs = qs.filter(bill_type=bill_type)
    if payment_status:
        qs = qs.filter(payment_status=payment_status)
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            qs = qs.filter(created_at__gte=sd)
        except Exception:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            qs = qs.filter(created_at__lte=ed)
        except Exception:
            pass
    if q:
        qs = qs.filter(Q(invoice_number__icontains=q) | Q(customer__customer_name__icontains=q) | Q(customer_name__icontains=q))

    # paginate
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 25)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'core/bill_list.html', {
        'bills': page_obj,
        'filter_bill_type': bill_type,
        'filter_payment_status': payment_status,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'q': q,
        'paginator': paginator,
        'page_obj': page_obj,
    })

@login_required
@user_passes_test(lambda u: check_permission(u, 'billing'))
def export_bills(request):
    if request.user.is_supervisor_or_admin() or request.user.has_module_access('billing'):
        qs = Bill.objects.all().order_by('-created_at')
    else:
        qs = Bill.objects.filter(created_by=request.user).order_by('-created_at')

    bill_type = request.GET.get('bill_type')
    payment_status = request.GET.get('payment_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if bill_type:
        qs = qs.filter(bill_type=bill_type)
    if payment_status:
        qs = qs.filter(payment_status=payment_status)
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            qs = qs.filter(created_at__gte=sd)
        except Exception:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            qs = qs.filter(created_at__lte=ed)
        except Exception:
            pass

    fmt = request.GET.get('format', 'csv')
    if fmt == 'csv':
        # stream CSV
        response = HttpResponse(content_type='text/csv')
        filename = f"bills_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['Invoice', 'Type', 'Customer', 'Created By', 'Created At (IST)', 'Total', 'Payment Status'])
        for bill in qs:
            created_ist = bill.created_at.astimezone(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
            customer = bill.customer.customer_name if bill.customer else (bill.customer_name or '')
            writer.writerow([bill.invoice_number, bill.get_bill_type_display(), customer, bill.created_by.username, created_ist, str(bill.total_amount), bill.get_payment_status_display()])
        return response
    elif fmt == 'pdf':
        if not WEASYPRINT_AVAILABLE:
            return HttpResponse('PDF export requires `weasyprint` package. Install with `pip install weasyprint`', status=400)
        # render html template and convert to pdf
        html_string = render_to_string('core/bill_export_pdf.html', {'bills': qs, 'now': datetime.now()})
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bills_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        return response
    else:
        return HttpResponse('Format not supported', status=400)

@login_required
@user_passes_test(lambda u: check_permission(u, 'billing'))
def edit_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if not (request.user.is_supervisor_or_admin() or bill.created_by == request.user or request.user.has_module_access('billing')):
        messages.error(request, "Unauthorized to edit this bill")
        return redirect('bill_list')
    if bill.bill_type == 'INNER':
        template_name = 'core/bill_form_inner.html'
    elif bill.bill_type == 'OUTER':
        template_name = 'core/bill_form_outer.html'
    else:
        template_name = 'core/bill_form_sales.html'

    items = Item.objects.all()
    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill)
        formset = BillItemFormSet(request.POST, instance=bill)
        payment_formset = BillPaymentFormSet(request.POST, instance=bill, prefix='payments')
        
        valid = form.is_valid() and formset.is_valid() and payment_formset.is_valid()

        if bill.bill_type in ['INNER', 'OUTER']:
            type_label = "Inner" if bill.bill_type == 'INNER' else "Outer"
            if not form.cleaned_data.get('customer'):
                form.add_error('customer', f"Customer is required for {type_label} Bills.")
                valid = False
            if not form.cleaned_data.get('delivery_date'):
                form.add_error('delivery_date', f"Delivery Date is required for {type_label} Bills.")
                valid = False

        # Specific validation for Sales Bill (Mobile Shop)
        if bill.bill_type == 'SALES':
            outlet = form.cleaned_data.get('outlet_name')
            if not outlet:
                 form.add_error('outlet_name', "Outlet is required for Sales bills.")
                 valid = False
            elif outlet in ['MOBILE_1', 'MOBILE_2', 'MOBILE_3']:
                if not form.cleaned_data.get('student_employees'):
                    form.add_error('student_employees', "Please select at least one student employee.")
                    valid = False

        if valid:
            # 1. Aggregate items first
            aggregated = {}
            for subform in formset:
                if not subform.cleaned_data or subform.cleaned_data.get('DELETE', False):
                    continue
                cd = subform.cleaned_data
                item = cd.get('item')
                custom_name = cd.get('custom_item_name') or ''
                qty = int(cd.get('quantity') or 0)
                price = cd.get('price')
                
                if qty <= 0:
                    continue

                if item and (price is None or price == ''):
                    price = item.price
                price = Decimal(price or 0)
                key = (f'item:{item.id}' if item else f'custom:{custom_name.strip()}', str(price))
                if key in aggregated:
                    aggregated[key]['quantity'] += qty
                else:
                    aggregated[key] = {'item': item, 'custom_item_name': custom_name, 'price': price, 'quantity': qty}

            # 2. Check if empty
            if not aggregated:
                # messages.error(request, "Cannot save a bill with no items. Please add at least one item.")
                form.add_error(None, "Cannot save a bill with no items. Please add at least one item.")
                items = Item.objects.all()
                items_mapping = {item.id: str(item.price) for item in items}
                if bill.bill_type == 'INNER':
                    template_name = 'core/bill_form_inner.html'
                elif bill.bill_type == 'OUTER':
                    template_name = 'core/bill_form_outer.html'
                else:
                    template_name = 'core/bill_form_sales.html'

                return render(request, template_name, {
                    'form': form,
                    'formset': formset,
                    'payment_formset': payment_formset, # ensure this is passed (not present in original but seems fine to pass)
                    'bill_type': bill.bill_type,
                    'items': items,
                    'items_json': json.dumps(items_mapping),
                    'editing': True,
                })

            # 2.5 Validation: Total Paid must match Grand Total for SALES bills (Only if PAID)
            if bill.bill_type == 'SALES':
                payment_status = form.cleaned_data.get('payment_status')
                if payment_status == 'PAID':
                    grand_total = Decimal('0')
                    for v in aggregated.values():
                        grand_total += v['price'] * v['quantity']
                    
                    total_paid = Decimal('0')
                    if payment_formset:
                        for p_form in payment_formset:
                            if p_form.cleaned_data and not p_form.cleaned_data.get('DELETE'):
                                 amount = p_form.cleaned_data.get('amount') or Decimal('0')
                                 if amount <= 0:
                                     p_form.add_error('amount', "Payment amount must be greater than 0.")
                                     # Force re-render if invalid
                                     items = Item.objects.all()
                                     items_mapping = {item.id: str(item.price) for item in items}
                                     return render(request, template_name, {
                                        'form': form,
                                        'formset': formset,
                                        'payment_formset': payment_formset,
                                        'bill_type': bill.bill_type,
                                        'items': items,
                                        'items_json': json.dumps(items_mapping),
                                        'editing': True,
                                    })
                                 total_paid += amount

                    if abs(total_paid - grand_total) > Decimal('0.5'):
                        form.add_error(None, f"Total Paid ({total_paid}) must match Grand Total ({grand_total}) for Paid Sales Bills.")
                        
                        items = Item.objects.all()
                        items_mapping = {item.id: str(item.price) for item in items}
                        return render(request, template_name, {
                            'form': form,
                            'formset': formset,
                            'payment_formset': payment_formset,
                            'bill_type': bill.bill_type,
                            'items': items,
                            'items_json': json.dumps(items_mapping),
                            'editing': True,
                        })

            # 3. Save Bill and Items
            bill = form.save(commit=False)
            bill.save()
            form.save_m2m() # Save student_employees relation
            
            # remove existing items and recreate grouped ones
            bill.items.all().delete()
            total = Decimal('0')
            for v in aggregated.values():
                bi = BillItem.objects.create(
                    bill=bill,
                    item=v['item'],
                    custom_item_name=v['custom_item_name'] or None,
                    quantity=v['quantity'],
                    price=v['price']
                )
                total += Decimal(bi.price) * bi.quantity
            bill.total_amount = total
            bill.save()
            
            # Save payments
            payments = payment_formset.save(commit=False)
            for payment in payments:
                payment.bill = bill
                payment.save()
            for obj in payment_formset.deleted_objects:
                obj.delete()

            messages.success(request, 'Bill updated successfully')
            return redirect('bill_detail', pk=bill.id)
    else:
        form = BillForm(instance=bill)
        formset = BillItemFormSet(instance=bill)
        payment_formset = BillPaymentFormSet(instance=bill, prefix='payments')
        if bill.bill_type == 'INNER':
            template_name = 'core/bill_form_inner.html'
        elif bill.bill_type == 'OUTER':
            template_name = 'core/bill_form_outer.html'
        else:
            template_name = 'core/bill_form_sales.html'
    items = Item.objects.all()
    items_mapping = {item.id: str(item.price) for item in items}
    return render(request, template_name, {
        'form': form,
        'formset': formset,
        'payment_formset': payment_formset,
        'bill_type': bill.bill_type,
        'items': items,
        'items_json': json.dumps(items_mapping),
        'editing': True,
    })

@login_required
@user_passes_test(lambda u: check_permission(u, 'billing'))
def delete_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if not (request.user.is_supervisor_or_admin() or bill.created_by == request.user or request.user.has_module_access('billing')):
        messages.error(request, "Unauthorized to delete this bill")
        return redirect('bill_list')
    if request.method == 'POST':
        bill.delete()
        messages.success(request, 'Bill deleted')
        return redirect('bill_list')
    return render(request, 'core/form_generic.html', {'form': None, 'title': f'Confirm Delete Invoice {bill.invoice_number}', 'object': bill})

@login_required
@user_passes_test(lambda u: check_permission(u, 'vendors'))
def vendor_list(request):
    vendors = Vendor.objects.all()
    return render(request, 'core/vendor_list.html', {'vendors': vendors})

@login_required
@user_passes_test(lambda u: check_permission(u, 'vendors'))
def create_vendor(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vendor created successfully")
            return redirect('vendor_list')
    else:
        form = VendorForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Add Vendor'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'vendors'))
def edit_vendor(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Vendor updated successfully")
            return redirect('vendor_list')
    else:
        form = VendorForm(instance=vendor)
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Edit Vendor'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'vendors'))
def delete_vendor(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.delete()
        messages.success(request, "Vendor deleted successfully")
        return redirect('vendor_list')
    return render(request, 'core/form_generic.html', {'form': None, 'title': f'Delete Vendor {vendor.name}', 'object': vendor})

@login_required
@user_passes_test(lambda u: check_permission(u, 'employees'))
def employee_list(request):
    employees = User.objects.filter(role__in=['EMPLOYEE', 'STUDENT'])
    return render(request, 'core/employee_list.html', {'employees': employees})

@login_required
@user_passes_test(lambda u: check_permission(u, 'employees'))
def edit_employee(request, pk):
    emp = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=emp)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee updated successfully")
            return redirect('employee_list')
    else:
        form = CustomUserCreationForm(instance=emp)
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Edit Employee'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'employees'))
def delete_employee(request, pk):
    emp = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        emp.is_active = False # Soft delete usually preferred for users
        emp.save()
        messages.success(request, "Employee deactivated")
        return redirect('employee_list')
    return render(request, 'core/form_generic.html', {'form': None, 'title': f'Deactivate Employee {emp.username}', 'object': emp})

@login_required
@user_passes_test(lambda u: check_permission(u, 'attendance'))
def attendance_list(request):
    # Base query with optimization
    if request.user.is_supervisor_or_admin() or request.user.role == 'ACCOUNTANT':
        logs = Attendance.objects.select_related('user').all().order_by('-date', '-in_time')
    else:
        logs = Attendance.objects.filter(user=request.user).order_by('-date', '-in_time')

    # Filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    user_id = request.GET.get('user_id')

    if start_date:
        try:
            sd = datetime.fromisoformat(start_date).date()
            logs = logs.filter(date__gte=sd)
        except ValueError:
            pass
    
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date).date()
            logs = logs.filter(date__lte=ed)
        except ValueError:
            pass

    if user_id and (request.user.is_supervisor_or_admin() or request.user.role == 'ACCOUNTANT'):
        logs = logs.filter(user_id=user_id)

    # Pagination
    paginator = Paginator(logs, 20) # Show 20 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check if user is currently clocked in
    current_attendance = Attendance.objects.filter(user=request.user, out_time__isnull=True, date=timezone.now().date()).first()
    
    # Get all users for filter dropdown (only for admins/accountants)
    users = User.objects.filter(role__in=['EMPLOYEE', 'STUDENT']) if (request.user.is_supervisor_or_admin() or request.user.role == 'ACCOUNTANT') else None

    return render(request, 'core/attendance_list.html', {
        'logs': page_obj, # Pass page_obj instead of all logs
        'current_attendance': current_attendance,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'filter_user_id': user_id,
        'users': users
    })

@login_required
@user_passes_test(lambda u: check_permission(u, 'attendance'))
def clock_in(request):
    if request.method == 'POST':
        # Check if already clocked in today
        today = timezone.now().date()
        existing = Attendance.objects.filter(user=request.user, out_time__isnull=True, date=today).first()
        if existing:
            messages.warning(request, "You are already clocked in.")
        else:
            Attendance.objects.create(
                user=request.user,
                date=today,
                in_time=timezone.now().time()
            )
            messages.success(request, "Clocked in successfully.")
    return redirect('attendance_list')

@login_required
@user_passes_test(lambda u: check_permission(u, 'attendance'))
def clock_out(request):
    if request.method == 'POST':
        today = timezone.now().date()
        # Find open attendance for today
        attendance = Attendance.objects.filter(user=request.user, out_time__isnull=True, date=today).first()
        if attendance:
            attendance.out_time = timezone.now().time()
            # Calculate duration
            dt_in = datetime.combine(today, attendance.in_time)
            dt_out = datetime.combine(today, attendance.out_time)
            diff = dt_out - dt_in
            hours = diff.total_seconds() / 3600
            attendance.total_hours = Decimal(hours)
            attendance.save()
            messages.success(request, "Clocked out successfully.")
        else:
            messages.error(request, "No active session found to clock out from.")
    return redirect('attendance_list')

@login_required
@user_passes_test(lambda u: check_permission(u, 'attendance'))
def approve_attendance(request):
    if not (request.user.is_supervisor_or_admin() or request.user.role == 'ACCOUNTANT'):
        messages.error(request, "Unauthorized")
        return redirect('attendance_list')
        
    if request.method == 'POST':
        attendance_id = request.POST.get('attendance_id')
        action = request.POST.get('action')
        attendance = get_object_or_404(Attendance, id=attendance_id)
        
        if action == 'approve':
            attendance.is_approved = True
            attendance.save()
            
            # Auto-create worklog for students
            if attendance.user.role == 'STUDENT' and attendance.total_hours:
                exists = StudentWorkLog.objects.filter(
                    student=attendance.user, 
                    date=attendance.date
                ).exists()
                
                if not exists:
                    StudentWorkLog.objects.create(
                        student=attendance.user,
                        date=attendance.date,
                        working_hours=attendance.total_hours,
                        overtime_hours=attendance.overtime_hours,
                        status='APPROVED'
                    )
                    messages.success(request, f"Attendance approved and Work Log created for {attendance.user.username}")
                else:
                    messages.success(request, f"Attendance approved. Work Log already exists for {attendance.user.username} on this date.")
            else:
                messages.success(request, "Attendance approved.")
                
        elif action == 'reject':
            attendance.is_approved = False 
            attendance.save()
            messages.warning(request, "Attendance rejected.")
            
        return redirect('approve_attendance')
    
    # GET request: Show pending approvals
    pending_attendance = Attendance.objects.filter(is_approved=False).order_by('-date', '-in_time')
    return render(request, 'core/attendance_approval.html', {'pending_logs': pending_attendance})

@login_required
@user_passes_test(lambda u: check_permission(u, 'attendance'))
def create_attendance(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            att = form.save(commit=False)
            att.user = request.user
            # Calculate total hours if out_time is present
            if att.out_time and att.in_time:
                # Simple calculation, assuming same day
                dummy_date = datetime.today().date()
                dt_in = datetime.combine(dummy_date, att.in_time)
                dt_out = datetime.combine(dummy_date, att.out_time)
                diff = dt_out - dt_in
                hours = diff.total_seconds() / 3600
                att.total_hours = Decimal(hours)
            att.save()
            messages.success(request, "Attendance logged")
            return redirect('attendance_list')
    else:
        form = AttendanceForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Log Attendance'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'worklogs'))
def worklog_list(request):
    if request.user.is_supervisor_or_admin() or request.user.role == 'ACCOUNTANT':
        logs = StudentWorkLog.objects.all().order_by('-date')
    else:
        logs = StudentWorkLog.objects.filter(student=request.user).order_by('-date')
    return render(request, 'core/worklog_list.html', {'logs': logs})

@login_required
@user_passes_test(lambda u: check_permission(u, 'worklogs'))
def create_worklog(request):
    if request.user.role != 'STUDENT':
        messages.error(request, "Only students can create work logs")
        return redirect('dashboard')
    if request.method == 'POST':
        form = StudentWorkLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.student = request.user
            log.save()
            messages.success(request, "Work log submitted for approval")
            return redirect('worklog_list')
    else:
        form = StudentWorkLogForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Submit Work Log'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'worklogs'))
def approve_worklog(request, pk):
    if request.user.role != 'ACCOUNTANT' and not request.user.is_supervisor_or_admin():
        messages.error(request, "Unauthorized")
        return redirect('worklog_list')
    log = get_object_or_404(StudentWorkLog, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            log.status = 'APPROVED'
        elif action == 'reject':
            log.status = 'REJECTED'
        log.save()
        return redirect('worklog_list')
    return render(request, 'core/form_generic.html', {'form': None, 'title': f'Approve Work Log for {log.student.username}', 'object': log})

@login_required
@user_passes_test(lambda u: check_permission(u, 'purchases'))
def purchase_list(request):
    purchases = PurchaseRecord.objects.all().order_by('-date')
    return render(request, 'core/purchase_list.html', {'purchases': purchases})

@login_required
@user_passes_test(lambda u: check_permission(u, 'purchases'))
def create_purchase(request):
    if request.method == 'POST':
        form = PurchaseRecordForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.purchased_by = request.user
            purchase.save()
            messages.success(request, "Purchase record created")
            return redirect('purchase_list')
    else:
        form = PurchaseRecordForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Record Purchase'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'vendors'))
def vendor_payment_list(request):
    payments = VendorPayment.objects.all().order_by('-date')
    return render(request, 'core/vendor_payment_list.html', {'payments': payments})

@login_required
@user_passes_test(lambda u: check_permission(u, 'vendors'))
def create_vendor_payment(request):
    if request.method == 'POST':
        form = VendorPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vendor payment recorded")
            return redirect('vendor_payment_list')
    else:
        form = VendorPaymentForm()
    return render(request, 'core/form_generic.html', {'form': form, 'title': 'Record Vendor Payment'})

@login_required
@user_passes_test(lambda u: check_permission(u, 'vendors'))
def approve_vendor_payment(request, pk):
    payment = get_object_or_404(VendorPayment, pk=pk)
    if request.method == 'POST':
        payment.approval_status = True
        payment.save()
        messages.success(request, "Payment approved")
        return redirect('vendor_payment_list')
    return render(request, 'core/form_generic.html', {'form': None, 'title': f'Approve Payment to {payment.vendor.name}', 'object': payment})

@login_required
@user_passes_test(lambda u: check_permission(u, 'reports'))
def payroll_summary(request):
    # Simple payroll calculation
    # For students: Sum of approved work logs * hourly rate (assuming fixed rate for now, or add to model)
    # For employees: Sum of attendance hours * hourly rate
    
    # Let's assume a fixed hourly rate for now or fetch from user profile if added.
    # Requirement says "Payroll Management" but doesn't specify rate storage.
    # I'll assume a default rate of 100 for now for demonstration.
    
    payroll_data = []
    
    # Students
    students = User.objects.filter(role='STUDENT')
    for student in students:
        logs = StudentWorkLog.objects.filter(student=student, status='APPROVED')
        total_hours = logs.aggregate(Sum('working_hours'))['working_hours__sum'] or 0
        overtime = logs.aggregate(Sum('overtime_hours'))['overtime_hours__sum'] or 0
        # Assuming rate 50 for students
        amount = (total_hours * 50) + (overtime * 75) # 1.5x for overtime
        payroll_data.append({
            'user': student,
            'role': 'Student',
            'total_hours': total_hours,
            'overtime': overtime,
            'amount': amount
        })
        
    # Employees
    employees = User.objects.filter(role='EMPLOYEE')
    for emp in employees:
        # Attendance based
        logs = Attendance.objects.filter(user=emp)
        total_hours = logs.aggregate(Sum('total_hours'))['total_hours__sum'] or 0
        # Assuming rate 100 for employees
        amount = total_hours * 100
        payroll_data.append({
            'user': emp,
            'role': 'Employee',
            'total_hours': total_hours,
            'overtime': 0, # Attendance model has overtime but logic needs to be defined
            'amount': amount
        })
        
    return render(request, 'core/payroll_summary.html', {'payroll_data': payroll_data})