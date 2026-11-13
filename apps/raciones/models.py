from django.db import models
from django.conf import settings


class racion_diaria(models.Model):
    fecha = models.DateField()
    turno = models.CharField(max_length=50)
    lote_id = models.ForeignKey('lotes_ganado.Lote', on_delete=models.CASCADE)
    usuario_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        db_table = 'racion_diaria'


class detalle_racion(models.Model):
    racion_id = models.ForeignKey('raciones.racion_diaria', on_delete=models.CASCADE)
    alimento_id = models.ForeignKey('alimentos.Alimento', on_delete=models.CASCADE)
    kg = models.DecimalField(max_digits=10, decimal_places=2)
    stock_insuficiente = models.BooleanField(default=False)

    class Meta:
        db_table = 'detalle_racion'