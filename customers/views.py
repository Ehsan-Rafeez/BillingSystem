from django.shortcuts import render
from django.views import View
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from customers.models import Customer as CustomerModel
from django.views.generic import TemplateView, CreateView, ListView, DeleteView, UpdateView
from django.urls import reverse_lazy
from .forms import CustomerForm
from django.contrib import messages

# Create your views here.


# List View for Customers
class CustomerListView(ListView):
    model = CustomerModel
    context_object_name = 'customers'
    template_name = 'customers/list_customer.html'  # Ensure this is correct
    paginate_by = 10  # Optional: for pagination

    def get_queryset(self):
        # You can filter or order the queryset here
        return CustomerModel.objects.all()  # Adjust as per your needs

# Create View for Customer
class CustomerCreateView(CreateView):
    model = CustomerModel
    form_class = CustomerForm
    template_name = "customers/create_customer.html"
    success_url = reverse_lazy("list_customer")

    def form_valid(self, form):
        # This method is called when the form is valid
        messages.success(self.request, "Customer created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        # This method is called when the form is invalid
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)

# Update View for Customer
class CustomerUpdateView(UpdateView):
    model = CustomerModel
    form_class = CustomerForm
    template_name = "customers/create_customer.html"
    success_url = reverse_lazy("list_customer")

    def form_valid(self, form):
        messages.success(self.request, "Customer updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)

# Delete View for Customer
class CustomerDeleteView(DeleteView):
    model = CustomerModel
    success_url = reverse_lazy("list_customer")
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = getattr(self.object, "name", "Customer")
        response = super().post(request, *args, **kwargs)  # performs the delete
        messages.success(request, f'"{name}" deleted successfully.')
        return response

# If needed, you can add a manual customer list view, but it's recommended to use the Class-Based Views above for better structure
def list_customer(request):
    customers = CustomerModel.objects.all()
    return render(request, 'customers/list_customer.html', {'customers': customers})

