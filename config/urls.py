from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('modulo/<slug:slug>/', views.modulo_detalle, name='modulo'),
    path('ejercicio/<int:pk>/', views.ejercicio, name='ejercicio'),
]
