from django.shortcuts import render

from ordersapp.models import Order  # apka model ka name ho sakta hai "Order"

def index(request):
    orders = Order.objects.all()  # database se saare orders le lo
    return render(request, 'core/index.html', {'orders': orders})
