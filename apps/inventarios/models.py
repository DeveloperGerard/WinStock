from django.conf import settings
from django.db import models


class Inventario(models.Model):
    clave = models.CharField(max_length=20, unique=True)  # alimentos, insumos, lotes
    nombre = models.CharField(max_length=50)
    usuarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="inventarios", blank=True
    )

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre