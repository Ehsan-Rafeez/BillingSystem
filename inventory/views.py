# inventory/views.py
from django.shortcuts import render

def add_stock(request):
    # Handle stock addition logic here
    return render(request, 'inventory/add_stock.html')

def list_stock(request):
    # Handle stock listing logic heresdad
    return render(request, 'inventory/list_stock.html')
