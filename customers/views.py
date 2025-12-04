from django.shortcuts import render
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from .models import Customer as CustomerModel
from .forms import CustomerForm

# List View for Customers with Search functionality
class CustomerListView(ListView):
    model = CustomerModel
    context_object_name = 'customers'
    template_name = 'customers/list_customer.html'
    paginate_by = 10  # Optional: for pagination

    def get_queryset(self):
        queryset = CustomerModel.objects.all()
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(cnic__icontains=query)
            )
        return queryset

# Create View for Customer
class CustomerCreateView(CreateView):
    model = CustomerModel
    form_class = CustomerForm
    template_name = 'customers/create_customer.html'
    success_url = reverse_lazy('list_customer')

    def form_valid(self, form):
        messages.success(self.request, "Customer created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)

# Update View for Customer
class CustomerUpdateView(UpdateView):
    model = CustomerModel
    form_class = CustomerForm
    template_name = 'customers/create_customer.html'
    success_url = reverse_lazy('list_customer')

    def form_valid(self, form):
        messages.success(self.request, "Customer updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)

# ✅ Delete View for Customer
class CustomerDeleteView(DeleteView):
    model = CustomerModel
    success_url = reverse_lazy('list_customer')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = getattr(self.object, 'name', 'Customer')
        messages.success(request, f'"{name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)
