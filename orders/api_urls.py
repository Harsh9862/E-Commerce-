from django.urls import path
from . import views

urlpatterns = [
    path('create-order/', views.api_create_order, name='api_create_order'),
    path('verify-payment/', views.api_verify_payment, name='api_verify_payment'),
]
