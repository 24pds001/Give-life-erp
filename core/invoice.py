from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Bill
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@login_required
def invoice_list(request):
    # supervisors and admin see all bills, others see only their own
    user = request.user
    if user.role in ['ADMIN', 'SUPERVISOR']:
        qs = Bill.objects.all().order_by('-created_at')
    else:
        qs = Bill.objects.filter(created_by=user).order_by('-created_at')

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
        # search invoice number or customer name
        qs = qs.filter(Q(invoice_number__icontains=q) | Q(customer__customer_name__icontains=q) | Q(customer_name__icontains=q))

    # Sorting
    if sort_by == 'date_asc':
        qs = qs.order_by('created_at')
    elif sort_by == 'date_desc':
        qs = qs.order_by('-created_at')
    elif sort_by == 'amount_asc':
        qs = qs.order_by('total_amount')
    elif sort_by == 'amount_desc':
        qs = qs.order_by('-total_amount')
    elif sort_by == 'invoice_asc':
        qs = qs.order_by('invoice_number')
    elif sort_by == 'invoice_desc':
        qs = qs.order_by('-invoice_number')

    # paginate
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 25)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'invoices': page_obj,
        'filter_bill_type': bill_type,
        'filter_payment_status': payment_status,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'sort_by': sort_by,
        'q': q,
        'paginator': paginator,
        'page_obj': page_obj,
    }
    return render(request, 'core/invoice_list.html', context)


@login_required
def invoice_export(request):
    user = request.user
    if user.role in ['ADMIN', 'SUPERVISOR']:
        qs = Bill.objects.all().order_by('-created_at')
    else:
        qs = Bill.objects.filter(created_by=user).order_by('-created_at')

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

    fmt = request.GET.get('format', 'csv')
    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        filename = f"invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['Invoice', 'Date (IST)', 'Customer', 'Bill Type', 'Total', 'Advance', 'Payment Type', 'Payment Status', 'Created By'])
        for b in qs:
            created_ist = b.created_at.astimezone(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
            customer = b.customer.customer_name if b.customer else (b.customer_name or '')
            writer.writerow([b.invoice_number, created_ist, customer, b.get_bill_type_display(), str(b.total_amount), str(b.advance_payment), b.payment_type, b.get_payment_status_display(), b.created_by.username])
        return response
    else:
        return HttpResponse('Only CSV export supported here', status=400)
