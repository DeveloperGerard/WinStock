from django import forms

from .models import Alimento


class AlimentoForm(forms.ModelForm):
    class Meta:
        model = Alimento
        fields = ("nombre", "stock")
        labels = {
            "nombre": "Nombre",
            "stock": "Stock actual",
        }
