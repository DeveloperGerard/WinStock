
from django.contrib import admin
from .models import Alimento, Movimientos_alimentos


@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "stock_actual",
        "stock_minimo",
        "stock_registrado",
        "estado"
    )

    search_fields = ("nombre",)
    list_filter = ("estado",)


@admin.register(Movimientos_alimentos)
class MovimientosAlimentosAdmin(admin.ModelAdmin):
    list_display = (
        "alimento",
        "cantidad",
        "fecha_movimiento",
        "usuario"
    )
