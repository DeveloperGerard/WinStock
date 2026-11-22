from django.db import models
from .models import Alimento

def alertas_stock(request):

    if not request.user.is_authenticated:
        return {
            "total_alertas_stock": 0
        }

    total_alertas = Alimento.objects.filter(
        estado=True,
        stock_actual__lte=models.F("stock_minimo")
    ).count()

    return {
        "total_alertas_stock": total_alertas
    }
