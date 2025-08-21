from django.urls import path, include

from .views import index
urlpatterns = [
    path('', index, name='index'),  # Home page view
    # Add other URL patterns here as needed
]