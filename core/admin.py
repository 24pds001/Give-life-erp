from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Item, Bill, BillItem, InventoryLog, Customer, Vendor, ActivityLog, Attendance, StudentWorkLog, PurchaseRecord, VendorPayment


class BillItemInline(admin.TabularInline):
	model = BillItem
	extra = 0
	fields = ('item', 'custom_item_name', 'quantity', 'price', 'total_display')
	readonly_fields = ('total_display',)

	def total_display(self, obj):
		return obj.quantity * obj.price
	total_display.short_description = 'Total'


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
	list_display = ('invoice_number', 'bill_type', 'customer_display', 'total_amount', 'payment_status', 'created_at', 'created_by')
	list_filter = ('bill_type', 'payment_status', 'created_at')
	search_fields = ('invoice_number', 'customer__shop_name', 'created_by__username')
	date_hierarchy = 'created_at'
	inlines = (BillItemInline,)
	actions = ('mark_as_paid',)
	list_select_related = ('customer', 'created_by')
	autocomplete_fields = ('customer',)

	def customer_display(self, obj):
		return obj.customer.shop_name if obj.customer else obj.customer_name
	customer_display.short_description = 'Customer'
	customer_display.admin_order_field = 'customer__shop_name'

	def mark_as_paid(self, request, queryset):
		updated = queryset.update(payment_status='PAID')
		self.message_user(request, f"{updated} bill(s) marked as PAID")
	mark_as_paid.short_description = 'Mark selected bills as PAID'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = ('shop_name', 'contact_number', 'gst_number')
	search_fields = ('shop_name', 'contact_number', 'gst_number')
	list_editable = ('contact_number', 'gst_number')
	ordering = ('shop_name',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
	list_display = ('name', 'price', 'is_active')
	search_fields = ('name',)
	list_editable = ('price', 'is_active')
	list_filter = ('is_active',)
	list_per_page = 50


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('vendor_id', 'name', 'contact', 'email', 'is_active')
    search_fields = ('name', 'vendor_id')
    list_filter = ('is_active',)

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('timestamp', 'user')
    search_fields = ('user__username', 'action')
    readonly_fields = ('user', 'action', 'timestamp')

    def has_add_permission(self, request):
        return False

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'in_time', 'out_time', 'total_hours', 'is_approved')
    list_filter = ('date', 'is_approved', 'user')

@admin.register(StudentWorkLog)
class StudentWorkLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'working_hours', 'status')
    list_filter = ('status', 'date')
    actions = ['approve_logs', 'reject_logs']

    def approve_logs(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_logs.short_description = "Approve selected logs"

    def reject_logs(self, request, queryset):
        queryset.update(status='REJECTED')
    reject_logs.short_description = "Reject selected logs"

@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'date', 'total_amount', 'purchased_by')
    list_filter = ('date', 'vendor')

@admin.register(VendorPayment)
class VendorPaymentAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'amount', 'date', 'status', 'approval_status')
    list_filter = ('status', 'approval_status', 'date')


admin.site.register(User, UserAdmin)
admin.site.register(InventoryLog)