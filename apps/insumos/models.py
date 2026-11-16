from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.
class Categoria(models.Model):
    CATEGORIAS = {
            'LubriFlui':'Lubricantes y fluidos',
            'FilRepue':'Filtros y repuestos',
            'ElemRepa':'Elementos de reparacion',
            'CompAcce':'Componentes y accesorios',
            'Comb':'Combustible'
        }
    categoria_id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=25,unique=True,choices=CATEGORIAS)
    descripcion= models.TextField()

    def __str__(self):
        return self.nombre
    

class Insumo(models.Model):
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


"""
Lubricantes y fluidos
Filtros y repuestos
Elementos de reparacion
Componentes y accesorios
Combustible
"""    
