from django.contrib import admin
from .models import Alimento, Movimientos_alimentos

@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "stock", "estado")
    search_fields = ("nombre",)
    list_filter = ("estado",)