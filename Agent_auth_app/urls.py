# Agent_auth_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('demo/', views.demo, name='demo'),
    path('live-security-analysis/', views.live_security_analysis, name='live_security_analysis'),
]