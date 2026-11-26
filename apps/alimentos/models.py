from django.db import models
from django.db.models import Q # Permite consutrir condiciones que django utiliza en conultas
from django.conf import settings

class Alimento(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ej: 99999999.99
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:#intrucciones adicionales para este modelo
        constraints = [ #restricciones
            models.CheckConstraint(
                condition=Q(stock__gte=0),
                name="stock_no_negativo"
            )
        ]


class Movimientos_alimentos(models.Model):
    id = models.AutoField(primary_key=True)
    alimento = models.ForeignKey(Alimento, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.alimento.nombre} - {self.cantidad} - {self.fecha_movimiento}"