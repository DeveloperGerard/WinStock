import uuid

from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.
class Categoria(models.Model):
    categoria_id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
    

class Insumo(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nombre = models.CharField(max_length=40,unique=True)
    cantidad = models.IntegerField(validators=[MinValueValidator(0)])
    unidad = models.CharField(
        choices=[
            ("Litros","Litros"),
            ("Kilogramos","Kilogramos"),
            ("Metros","Metros"),
            ("Unidades","Unidades")]
        )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        db_column="categoria_id",
        null=True,
        blank=True
        )

    def __str__(self):
        return self.nombre

