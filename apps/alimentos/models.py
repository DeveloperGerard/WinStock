from django.db import models
from django.conf import settings

# Modelo de Alimentos
class Alimento(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    stock_registrado = models.CharField(max_length=20, default="kg")
    estado = models.BooleanField(default=True)


    def __str__(self):
        return self.nombre

class Movimientos_alimentos(models.Model):
    id = models.AutoField(primary_key=True)
    alimento = models.ForeignKey(Alimento, on_delete=models.CASCADE)
    cantidad = models.FloatField()
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.alimento.nombre} - {self.cantidad} - {self.fecha_movimiento}"