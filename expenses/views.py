import csv
from decimal import Decimal
from datetime import datetime, time, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from django.utils import timezone

from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, ExpenseCategoryForm


def _parse_date_any(val):
    if not val:
        return None
    d = parse_date(val)
    if d:
        return d
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def expense_list(request):
    expenses = Expense.objects.select_related("category").all()
    return render(request, "expenses/expense_list.html", {"expenses": expenses})


def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense recorded.")
            return redirect("expense_list")
        messages.error(request, "Please fix errors below.")
    else:
        form = ExpenseForm()
    return render(request, "expenses/expense_form.html", {"form": form, "is_edit": False})


def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated.")
            return redirect("expense_list")
        messages.error(request, "Please fix errors below.")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, "expenses/expense_form.html", {"form": form, "is_edit": True, "expense": expense})


def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted.")
        return redirect("expense_list")
    return render(request, "expenses/expense_confirm_delete.html", {"expense": expense})


def expense_report(request):
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    download = request.GET.get("download")
    category_id = request.GET.get("category")

    start = _parse_date_any(start_raw)
    end = _parse_date_any(end_raw)
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, time.min), tz) if start else None
    end_dt = timezone.make_aware(datetime.combine(end, time.max), tz) if end else None

    qs = Expense.objects.select_related("category").all()
    if start_dt and end_dt:
        qs = qs.filter(date__range=(start, end))
    elif start_dt:
        qs = qs.filter(date__gte=start)
    elif end_dt:
        qs = qs.filter(date__lte=end)
    if category_id:
        qs = qs.filter(category_id=category_id)

    rows = list(qs.order_by("-date", "-id"))
    total = sum([exp.amount for exp in rows], Decimal("0.00")) if rows else Decimal("0.00")

    if download == "csv":
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="expense_report.csv"'
        writer = csv.writer(resp)
        writer.writerow(["Date", "Category", "Description", "Amount", "Supplier", "Reference", "Payment Method"])
        for exp in rows:
            writer.writerow([exp.date, exp.category.name if exp.category else "", exp.description, exp.amount, exp.supplier_name, exp.reference, exp.get_payment_method_display()])
        return resp

    return render(request, "expenses/expense_report.html", {
        "rows": rows,
        "total": total,
        "start": start_raw,
        "end": end_raw,
        "categories": ExpenseCategory.objects.order_by("name"),
        "selected_category": category_id,
    })


def expense_category_list(request):
    categories = ExpenseCategory.objects.order_by("name")
    return render(request, "expenses/category_list.html", {"categories": categories})


def expense_category_create(request):
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created.")
            return redirect("expense_category_list")
        messages.error(request, "Please fix errors below.")
    else:
        form = ExpenseCategoryForm()
    return render(request, "expenses/category_form.html", {"form": form, "is_edit": False})


def expense_category_update(request, pk):
    category = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("expense_category_list")
        messages.error(request, "Please fix errors below.")
    else:
        form = ExpenseCategoryForm(instance=category)
    return render(request, "expenses/category_form.html", {"form": form, "is_edit": True, "category": category})
