from django.urls import path

from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('settings/', views.shop_settings, name='shop_settings'),
]
