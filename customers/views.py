from django.shortcuts import render
from django.views import View
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from customers.models import Customer as CustomerModel
from django.views.generic import TemplateView , CreateView, ListView, DeleteView, UpdateView
from django.urls import reverse_lazy
from .forms import CustomerForm
from django.contrib import messages

# Create your views here.

def customers_index(request):
    return render(request, 'index_customer.html')


def list_customer(request):
    # Logic to list customers
    return render(request, 'list_customer.html')

# def create_customer(request):
#     # Logic to create a new customer
#     return render(request, 'create_customer.html')


class Customer(View):
    # Logic for customer creation
    def get(self, request):

        return render(request, 'create_customer.html')
    def post(self, request):
        print('post')
        # Process the form data
        fullname = request.POST.get('fullname', '').strip()
        customer_type = request.POST.get('customerType', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        errors = {}

        if not fullname:
            errors['fullname'] = 'First name is required.'
        if customer_type not in ['individual', 'company']:
            errors['customerType'] = 'Invalid customer type.'
        if not phone or not phone.isdigit():
            errors['phone'] = 'Valid phone number is required.'
        if not email or '@' not in email:
            errors['email'] = 'Valid email is required.'

        if errors:
            return render(request, 'create_customer.html', {'errors': errors, 'form_data': request.POST})

        customer = CustomerModel(
            name=fullname,
            customer_type=customer_type,
            phone=phone,
            email=email,
            address=address
        )
        customer.save()

        # Handle form submission for creating a customer
        # Save the customer data to the database
        return render(request, 'success.html')



class CustomerIndexView(TemplateView):
    template_name = 'customers_index.html'

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['customers'] = CustomerModel.objects.all()
    #     return context



class CustomerCreateView(CreateView):
    print('function called')
    model = CustomerModel
    form_class = CustomerForm
    template_name = "create_customer.html"
    success_url = reverse_lazy("customer_list")

    def dispatch(self, request, *args, **kwargs):
        print("[CustomerCreateView] dispatch:", request.method)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        print("[CustomerCreateView] GET")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("[CustomerCreateView] POST data:", dict(request.POST))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        print("[CustomerCreateView] form_valid -> will redirect to", self.success_url)
        messages.success(self.request, "Customer created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        print("[CustomerCreateView] form_invalid errors:", form.errors.as_json())
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)
    

class CustomerListView(ListView):
    model = CustomerModel
    context_object_name = 'customers'
    template_name = 'customer_list.html'
    paginate_by = 10  # Optional: for pagination

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['customers'] = CustomerModel.objects.all()
    #     return context
    

class CustomerUpdateView(UpdateView):
    model = CustomerModel
    form_class = CustomerForm
    template_name = "create_customer.html"
    success_url = reverse_lazy("customer_list")

    def form_valid(self, form):
        messages.success(self.request, "Customer updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)


class CustomerDeleteView(DeleteView):
    model = CustomerModel
    # template_name = "customer_confirm_delete.html" 
    http_method_names = ["post"]
    # template_name = "customer_list.html"
    success_url = reverse_lazy("customer_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = getattr(self.object, "name", "Customer")
        response = super().post(request, *args, **kwargs)  # does the delete
        messages.success(request, f'"{name}" deleted.')
        return response