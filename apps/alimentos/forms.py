from django import forms

from .models import Alimento


class AlimentoForm(forms.ModelForm):
    class Meta:
        model = Alimento
        fields = ("nombre", "stock_registrado")
        labels = {
            "nombre": "Nombre",
            "stock_registrado": "Stock registrado",
        }
