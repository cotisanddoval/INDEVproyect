from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from .models import Ejercicio, Modulo


def completados_de(request):
    """Ids de los ejercicios que el usuario ya resolvió bien."""
    return set(request.session.get("completados", []))


def home(request):
    modulos = Modulo.objects.annotate(total_ejercicios=Count("ejercicios"))
    return render(request, "core/home.html", {"modulos": modulos})


def modulo_detalle(request, slug):
    modulo = get_object_or_404(Modulo, slug=slug)
    completados = completados_de(request)
    ejercicios = list(modulo.ejercicios.order_by("pk"))

    anterior_ok = True
    for ej in ejercicios:
        ej.completado = ej.pk in completados
        ej.disponible = ej.completado or anterior_ok
        anterior_ok = ej.completado

    return render(request, "core/modulo.html", {"modulo": modulo, "ejercicios": ejercicios})


def ejercicio(request, pk):
    ej = get_object_or_404(Ejercicio, pk=pk)
    completados = completados_de(request)

    anterior = (
        Ejercicio.objects.filter(modulo=ej.modulo, pk__lt=ej.pk).order_by("-pk").first()
    )
    if anterior and anterior.pk not in completados and ej.pk not in completados:
        messages.warning(request, "Primero tenés que resolver bien el ejercicio anterior.")
        return redirect("modulo", slug=ej.modulo.slug)

    resultado = None
    if request.method == "POST":
        respuesta = request.POST.get("respuesta", "")
        resultado = ej.corregir(respuesta)
        if resultado:
            completados.add(ej.pk)
            request.session["completados"] = list(completados)

    siguiente = (
        Ejercicio.objects.filter(modulo=ej.modulo, pk__gt=ej.pk).order_by("pk").first()
    )
    return render(request, "core/ejercicio.html", {
        "ejercicio": ej,
        "resultado": resultado,
        "siguiente": siguiente,
    })