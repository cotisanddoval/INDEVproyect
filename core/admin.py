from django.contrib import admin
from .models import Modulo, Ejercicio, Opcion, Progreso


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 4


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ("enunciado", "modulo", "tipo", "nivel")
    list_filter = ("modulo", "tipo", "nivel")
    inlines = [OpcionInline]


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ("nombre", "orden")
    prepopulated_fields = {"slug": ("nombre",)}
    
@admin.register(Progreso)
class ProgresoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "ejercicio", "fecha")
    list_filter = ("usuario",)