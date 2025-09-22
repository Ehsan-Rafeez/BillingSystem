from django.shortcuts import render

# Create your views here.from django.shortcuts import render

def create_orders(request):
    return render(request, 'create_orders.html')


def list_orders(request):
    return render(request, 'list_orders.html')