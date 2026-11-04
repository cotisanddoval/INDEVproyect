from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegistroForm
from .models import Ejercicio, Modulo, Progreso

CONSIGNAS = {
    Ejercicio.SELECCION: "Elegí la opción correcta.",
    Ejercicio.COMPLETAR: "Escribí la palabra que falta.",
    Ejercicio.VERDADERO_FALSO: "Indicá si la frase es verdadera o falsa.",
}


def completados_de(usuario):
    """Ids de los ejercicios que el usuario ya resolvió bien."""
    return set(
        Progreso.objects.filter(usuario=usuario).values_list("ejercicio_id", flat=True)
    )


def home(request):
    modulos = Modulo.objects.all()
    return render(request, "core/home.html", {"modulos": modulos})


def registro(request):
    if request.user.is_authenticated:
        return redirect("panel")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect("panel")
    else:
        form = RegistroForm()

    return render(request, "cuentas/registro.html", {"form": form})


@login_required
def panel(request):
    completados = completados_de(request.user)
    modulos = list(Modulo.objects.prefetch_related("ejercicios"))

    total_global = 0
    hechos_global = 0
    modulos_completos = 0
    siguiente = None

    for m in modulos:
        ejercicios = sorted(m.ejercicios.all(), key=lambda e: e.pk)
        m.total = len(ejercicios)
        m.hechos = sum(1 for e in ejercicios if e.pk in completados)
        m.porcentaje = round(m.hechos * 100 / m.total) if m.total else 0
        m.completo = m.total > 0 and m.hechos == m.total
        m.empezado = m.hechos > 0

        total_global += m.total
        hechos_global += m.hechos
        if m.completo:
            modulos_completos += 1
        if siguiente is None:
            siguiente = next((e for e in ejercicios if e.pk not in completados), None)

    return render(request, "core/panel.html", {
        "modulos": modulos,
        "siguiente": siguiente,
        "hechos_global": hechos_global,
        "total_global": total_global,
        "porcentaje_global": round(hechos_global * 100 / total_global) if total_global else 0,
        "modulos_completos": modulos_completos,
        "total_modulos": len(modulos),
    })

@login_required
def modulo_detalle(request, slug):
    modulo = get_object_or_404(Modulo, slug=slug)
    completados = completados_de(request.user)
    ejercicios = list(modulo.ejercicios.order_by("pk"))

    anterior_ok = True
    hechos = 0
    for ej in ejercicios:
        ej.completado = ej.pk in completados
        ej.disponible = ej.completado or anterior_ok
        ej.actual = ej.disponible and not ej.completado
        if ej.completado:
            hechos += 1
        anterior_ok = ej.completado

    total = len(ejercicios)
    porcentaje = round(hechos * 100 / total) if total else 0

    return render(request, "core/modulo.html", {
        "modulo": modulo,
        "ejercicios": ejercicios,
        "hechos": hechos,
        "total": total,
        "porcentaje": porcentaje,
        "terminado": total > 0 and hechos == total,
    })


@login_required
def ejercicio(request, pk):
    ej = get_object_or_404(Ejercicio, pk=pk)
    completados = completados_de(request.user)

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
            Progreso.objects.get_or_create(usuario=request.user, ejercicio=ej)

    ids = list(
        Ejercicio.objects.filter(modulo=ej.modulo).order_by("pk").values_list("pk", flat=True)
    )
    numero = ids.index(ej.pk) + 1
    total = len(ids)
    siguiente = (
        Ejercicio.objects.filter(modulo=ej.modulo, pk__gt=ej.pk).order_by("pk").first()
    )

    return render(request, "core/ejercicio.html", {
        "ejercicio": ej,
        "resultado": resultado,
        "siguiente": siguiente,
        "consigna": CONSIGNAS.get(ej.tipo, ""),
        "numero": numero,
        "total": total,
        "porcentaje": round(numero * 100 / total),
    })