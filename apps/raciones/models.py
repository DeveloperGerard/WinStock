from django.db import models

# Create your models here.

class detalle_racion(models.Model):
    id_detalle_racion = models.AutoField(primary_key=True)
    id_racion = models.ForeignKey('raciones.racion', on_delete=models.CASCADE)
    id_alimento = models.ForeignKey('productos.producto', on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    stock_insuficiente = models.BooleanField(default=False)

    class Meta:
        db_table = 'detalle_racion'

class racion_diaria(models.Model):
    id_racion_diaria = models.AutoField(primary_key=True)
    fecha = models.DateField()
    id_racion = models.ForeignKey('raciones.racion', on_delete=models.CASCADE)

    class Meta:
        db_table = 'racion_diaria'