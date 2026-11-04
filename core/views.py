
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

NIVELES_ORDEN = ["A1", "A2", "B1"]

NOMBRES_NIVELES = {
    "A1": "Beginner",
    "A2": "Elementary",
    "B1": "Intermediate",
}


def completados_de(usuario):
    """Ids de los ejercicios que el usuario ya resolvió bien."""
    return set(
        Progreso.objects.filter(usuario=usuario).values_list(
            "ejercicio_id", flat=True
        )
    )


def nivel_actual_de(completados):
    """Devuelve el primer nivel que el usuario todavía no completó."""

    for nivel in NIVELES_ORDEN:
        ids = set(
            Ejercicio.objects.filter(nivel=nivel).values_list(
                "pk", flat=True
            )
        )

        # Si todavía no hay actividades, ese será el próximo nivel.
        if not ids:
            return nivel

        # Si falta completar al menos un ejercicio, seguimos en ese nivel.
        if not ids.issubset(completados):
            return nivel

    return NIVELES_ORDEN[-1]


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
    nivel_actual = nivel_actual_de(completados)

    modulos = list(
        Modulo.objects.prefetch_related("ejercicios")
    )

    total_global = 0
    hechos_global = 0
    modulos_completos = 0
    siguiente = None

    for m in modulos:
        # Solo contamos los ejercicios del nivel actualmente habilitado.
        ejercicios = sorted(
            [
                e for e in m.ejercicios.all()
                if e.nivel == nivel_actual
            ],
            key=lambda e: e.pk
        )

        m.total = len(ejercicios)
        m.hechos = sum(
            1 for e in ejercicios if e.pk in completados
        )
        m.porcentaje = (
            round(m.hechos * 100 / m.total)
            if m.total else 0
        )
        m.completo = (
            m.total > 0 and m.hechos == m.total
        )
        m.empezado = m.hechos > 0

        total_global += m.total
        hechos_global += m.hechos

        if m.completo:
            modulos_completos += 1

        if siguiente is None:
            siguiente = next(
                (e for e in ejercicios if e.pk not in completados),
                None
            )

    porcentaje_global = (
        round(hechos_global * 100 / total_global)
        if total_global else 0
    )

    return render(request, "core/panel.html", {
        "modulos": modulos,
        "siguiente": siguiente,
        "hechos_global": hechos_global,
        "total_global": total_global,
        "porcentaje_global": porcentaje_global,
        "modulos_completos": modulos_completos,
        "total_modulos": len(modulos),
        "nivel_actual": nivel_actual,
        "nombre_nivel": NOMBRES_NIVELES[nivel_actual],
    })


@login_required
def modulo_detalle(request, slug):
    modulo = get_object_or_404(Modulo, slug=slug)

    completados = completados_de(request.user)
    nivel_actual = nivel_actual_de(completados)

    # Por ahora se muestran solamente los ejercicios del nivel habilitado.
    ejercicios = list(
        modulo.ejercicios.filter(
            nivel=nivel_actual
        ).order_by("pk")
    )

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

    porcentaje = (
        round(hechos * 100 / total)
        if total else 0
    )

    return render(request, "core/modulo.html", {
        "modulo": modulo,
        "ejercicios": ejercicios,
        "hechos": hechos,
        "total": total,
        "porcentaje": porcentaje,
        "terminado": total > 0 and hechos == total,
        "nivel_actual": nivel_actual,
        "nombre_nivel": NOMBRES_NIVELES[nivel_actual],
    })


@login_required
def ejercicio(request, pk):
    ej = get_object_or_404(Ejercicio, pk=pk)

    completados = completados_de(request.user)
    nivel_actual = nivel_actual_de(completados)

    # No permitir entrar a niveles superiores al habilitado.
    if (
        ej.nivel not in NIVELES_ORDEN
        or NIVELES_ORDEN.index(ej.nivel)
        > NIVELES_ORDEN.index(nivel_actual)
    ):
        messages.warning(
            request,
            "Primero tenés que completar los niveles anteriores."
        )
        return redirect("panel")

    # Comprobar el ejercicio anterior del mismo módulo y nivel.
    anterior = (
        Ejercicio.objects.filter(
            modulo=ej.modulo,
            nivel=ej.nivel,
            pk__lt=ej.pk
        )
        .order_by("-pk")
        .first()
    )

    if (
        anterior
        and anterior.pk not in completados
        and ej.pk not in completados
    ):
        messages.warning(
            request,
            "Primero tenés que resolver bien el ejercicio anterior."
        )
        return redirect("modulo", slug=ej.modulo.slug)

    resultado = None

    if request.method == "POST":
        respuesta = request.POST.get("respuesta", "")
        resultado = ej.corregir(respuesta)

        if resultado:
            Progreso.objects.get_or_create(
                usuario=request.user,
                ejercicio=ej
            )

    ids = list(
        Ejercicio.objects.filter(
            modulo=ej.modulo,
            nivel=ej.nivel
        )
        .order_by("pk")
        .values_list("pk", flat=True)
    )

    numero = ids.index(ej.pk) + 1
    total = len(ids)

    siguiente = (
        Ejercicio.objects.filter(
            modulo=ej.modulo,
            nivel=ej.nivel,
            pk__gt=ej.pk
        )
        .order_by("pk")
        .first()
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
