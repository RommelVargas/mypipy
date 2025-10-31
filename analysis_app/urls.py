# fluid_calculator/analysis_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.calculate_fluid_flow, name='flow_calculator'),
]