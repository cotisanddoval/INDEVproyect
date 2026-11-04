from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from core import views
from core.forms import IngresoForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('modulo/<slug:slug>/', views.modulo_detalle, name='modulo'),
    path('ejercicio/<int:pk>/', views.ejercicio, name='ejercicio'),
    path('registro/', views.registro, name='registro'),
    path('ingresar/', auth_views.LoginView.as_view(
        template_name='cuentas/login.html',
        authentication_form=IngresoForm,
        redirect_authenticated_user=True,
    ), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
        path('panel/', views.panel, name='panel'),
]