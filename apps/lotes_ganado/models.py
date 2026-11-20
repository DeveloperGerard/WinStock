from django.db import models
import uuid

class Lote(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nombre = models.CharField(max_length=100, verbose_name='Nombre del lote', blank=True )
    cantidad = models.IntegerField(verbose_name='Cantidad de animales', default=1,  blank=False, null=False)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.nombre} - {self.cantidad}'
