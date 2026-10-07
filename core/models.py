from django.core.exceptions import ValidationError
from django.db import models


class Modulo(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(
        max_length=50, default="bi-book",
        help_text="Clase de Bootstrap Icons, ej: bi-briefcase"
    )
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden"]

    def __str__(self):
        return self.nombre


class Ejercicio(models.Model):
    SELECCION = "seleccion"
    COMPLETAR = "completar"
    VERDADERO_FALSO = "vf"
    TIPOS = [
        (SELECCION, "Selección múltiple"),
        (COMPLETAR, "Completar (fill in the gaps)"),
        (VERDADERO_FALSO, "Verdadero o falso"),
    ]

    NIVELES = [
        ("A1", "A1 - Principiante"),
        ("A2", "A2 - Elemental"),
        ("B1", "B1 - Intermedio"),
        ("B2", "B2 - Intermedio alto"),
    ]

    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name="ejercicios")
    tipo = models.CharField(max_length=10, choices=TIPOS, default=SELECCION)
    nivel = models.CharField(max_length=2, choices=NIVELES, default="A1")
    enunciado = models.TextField(
        help_text="En 'completar', usá ___ (tres guiones bajos) donde va el hueco."
    )
    respuesta_correcta = models.CharField(
        max_length=200, blank=True,
        help_text="Solo para 'completar'. Si hay varias respuestas válidas, separalas con |"
    )
    es_verdadero = models.BooleanField(
        null=True, blank=True,
        help_text="Solo para 'verdadero o falso'."
    )
    explicacion = models.TextField(
        blank=True, help_text="Opcional: se muestra después de responder."
    )

    def __str__(self):
        return self.enunciado[:60]

    def clean(self):
        if self.tipo == self.COMPLETAR:
            if "___" not in self.enunciado:
                raise ValidationError("El enunciado debe incluir ___ donde va el hueco.")
            if not self.respuesta_correcta:
                raise ValidationError("Falta la respuesta correcta.")
        if self.tipo == self.VERDADERO_FALSO and self.es_verdadero is None:
            raise ValidationError("Indicá si la afirmación es verdadera o falsa.")

    def corregir(self, respuesta):
        """Devuelve True si la respuesta del usuario es correcta."""
        respuesta = str(respuesta or "").strip()

        if self.tipo == self.SELECCION:
            return respuesta.isdigit() and self.opciones.filter(
                pk=int(respuesta), es_correcta=True
            ).exists()

        if self.tipo == self.COMPLETAR:
            validas = [r.strip().lower() for r in self.respuesta_correcta.split("|")]
            return respuesta.lower() in validas

        if self.tipo == self.VERDADERO_FALSO:
            return respuesta in ("true", "false") and (respuesta == "true") == self.es_verdadero

        return False


class Opcion(models.Model):
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE, related_name="opciones")
    texto = models.CharField(max_length=200)
    es_correcta = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "opciones"

    def __str__(self):
        return self.texto